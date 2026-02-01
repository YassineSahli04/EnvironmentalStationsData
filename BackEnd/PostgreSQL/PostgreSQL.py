from datetime import datetime
import json
import sqlalchemy.engine as _engine
from sqlalchemy import create_engine, text, bindparam
import os
from BackEnd.GeoJson.GeoJsonStationInfoFeature import GeoJsonStationInfoFeature
from BackEnd.PostgreSQL.StationDbObject import StationDbObject, StationState
from BackEnd.C2aiStations.Api.C2aiTableCreator import C2aiTableCreator
from BackEnd.GeoJson.GeoJsonObject import GeoJsonObject
from BackEnd.ClimateFieldStations.API.CfTableCreator import CfTableCreator
from concurrent.futures import ThreadPoolExecutor
from BackEnd.Utils.EmailNotifier import EmailNotifier
from BackEnd.PostgreSQL.User import User

class PostgreSQL:
    engine: _engine.Engine;
    CHUNK_SIZE = 25
    def __init__(self):
        self.SECRETJSONPATH = os.getenv("DBINFO_PATH")
        self.initialize_postgres_connection()   

    def initialize_postgres_connection(self):
        if self.SECRETJSONPATH is None:
            raise RuntimeError("DBINFO_PATH env var is not set")
        if not os.path.exists(self.SECRETJSONPATH):
            raise RuntimeError(f"Secret file not found: {self.SECRETJSONPATH}")

        with open(self.SECRETJSONPATH, "r") as f:
            data = json.load(f)

        
        userName = data.get("userName")
        password = data.get("password")
        host = data.get("host")
        port = data.get("port")
        database = data.get("database")

        connection_string = f"postgresql+psycopg2://{userName}:{password}@{host}:{port}/{database}"
        self.engine = create_engine(
            connection_string,
            connect_args={"options": "-c timezone=UTC"},
        )
    
    def get_all_station_objects(self, typeFilter = None) -> list[StationDbObject]:
        query = text("SELECT DISTINCT  \"StationId\" FROM \"Stations\";")
        if typeFilter:
            query = (text(f"SELECT DISTINCT  \"StationId\" FROM \"Stations\" WHERE \"Type\" IN :types;").bindparams(bindparam("types", expanding=True)))
        stations = []
        with self.engine.connect() as connection:
            if typeFilter:
                result = connection.execute(query, {"types":typeFilter}).fetchall()
            else:
                result = connection.execute(query).fetchall()
            for res in result:
                station_id = int(res[0])
                station = StationDbObject(self.engine, station_id)
                stations.append(station)
        return stations
    
    def get_all_user_objects(self) -> list[User]:
        query = text("SELECT \"Name\" FROM \"Users\";")
        users = []
        with self.engine.connect() as connection:
            result = connection.execute(query).fetchall()
            for res in result:
                userName = res[0]
                user = User(self.engine, userName)
                users.append(user)
        return users
    
    def create_update_all_stations_data_tables(self):
        stations = self.get_all_station_objects()
        users = self.get_all_user_objects()
        userEmailsToAlert = [user.Email for user in users if user.IsSubscribedToStationAlerts]
        for station in stations:
            for hardwareStation in station.HardwareStationIds: # type: ignore
                match station.Manufacturer:
                    case "DeltaOHM":
                        if station.DataSourceId is None:
                            raise ValueError(f"Station {station.Id} does not have a DataSourceId.")
                        table_creator = C2aiTableCreator(self.engine, station.DataSourceId)
                        alreadyExists = table_creator.create_postgre_table()
                        
                    case "Pessl":
                        table_creator = CfTableCreator(self.engine, hardwareStation)
                        alreadyExists = table_creator.IsDataTableCreated()

                if not alreadyExists:
                    dataDf = table_creator.getFullDataDf()
                    self.insert_create_data_df(dataDf, table_creator.newTableName)
                else:
                    self.update_db_table(
                        station.Manufacturer,
                        station.Id,
                        station.DataSourceId,
                        station.LastDataPointTime,
                    )

            station.addVpdColOrUpdate()
            
            station.updateStationState()
            if station.HasStateChanged:
                self.update_station_state(station, userEmailsToAlert)

    def insert_create_data_df(self, df, tableName):
        with self.engine.begin() as connection:
            connection.execute(text("SET TIME ZONE 'UTC';"))
            if(df is not None):
                df.to_sql(
                    name=tableName,
                    con=connection,
                    if_exists="append",
                    index=False, 
                    method="multi",
                    chunksize=self.CHUNK_SIZE,
                )
            
            query = text(f"""
                DO $$
                BEGIN
                    IF to_regclass('public."{tableName}"') IS NOT NULL THEN
                        IF NOT EXISTS (
                            SELECT 1
                            FROM pg_constraint c
                            WHERE c.conrelid = to_regclass('public."{tableName}"')
                            AND c.contype = 'p'
                        ) THEN
                            ALTER TABLE "{tableName}"
                            ADD CONSTRAINT "{tableName}_pkey" PRIMARY KEY (date_time);
                        END IF;
                    END IF;
                END $$;
                """)
            connection.execute(query)
        
    def get_stations_Geojson_object(self, typeFilter = None):
        stations = self.get_all_station_objects(typeFilter)

        with ThreadPoolExecutor(max_workers=8) as ex:
            features = list(ex.map(GeoJsonStationInfoFeature, stations))

        geoJson =  GeoJsonObject()
        for feature in features:
            geoJson.add_feature(feature) # type: ignore
        return geoJson.to_dict()

    def update_db_table(
        self,
        manufacturer: str | None,
        hardwareId: int,
        datasource_id: int | None,
        last_data_point_time: datetime| None,
    ):
        match manufacturer:
            case "DeltaOHM":
                if datasource_id is None:
                    raise ValueError(f"DeltaOHM Station {hardwareId} does not have a DataSourceId.")
                table_creator = C2aiTableCreator(self.engine, datasource_id)
            case "Pessl":
                table_creator = CfTableCreator(self.engine, str(hardwareId))
            case _:
                raise Exception("Data Tables are only available for DeltaOHM Stations and Pessl")

        dataDf = table_creator.getFullDataDf(last_data_point_time)  # type: ignore
        self.insert_create_data_df(dataDf, table_creator.newTableName)

    def update_station_state(self, station: StationDbObject, userEmailsToAlert: list[str]):
        query = text("UPDATE \"Stations\" SET \"State\" = :state WHERE \"StationId\" = :station_id;")
        with self.engine.begin() as connection:
            connection.execute(query, {"station_id": station.Id, "state": station.State.value}) # type: ignore
        self._send_state_change_notification(station, userEmailsToAlert)

    def _send_state_change_notification(self, station: StationDbObject, userEmailsToAlert: list[str]):
        notifier = EmailNotifier(userEmailsToAlert)
        notifier.send_station_state_change_email(station)
