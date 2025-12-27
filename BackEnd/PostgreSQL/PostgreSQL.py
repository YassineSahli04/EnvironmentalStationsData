import json
import sqlalchemy.engine as _engine
from sqlalchemy import create_engine, text, bindparam, event
import os
from BackEnd.GeoJson.GeoJsonStationInfoFeature import GeoJsonStationInfoFeature
from BackEnd.PostgreSQL.StationDbObject import StationDbObject
from BackEnd.C2aiStations.C2aiApi.C2aiTableCreator import C2aiTableCreator
from BackEnd.GeoJson.GeoJsonObject import GeoJsonObject
from datetime import timezone
from BackEnd.ClimateFieldStations.API.CfTableCreator import CfTableCreator

class PostgreSQL:
    engine: _engine.Engine;
    CHUNK_SIZE = 5000
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
        self.engine = create_engine(connection_string)

        @event.listens_for(self.engine, "connect")
        def _set_sql_timezone(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("SET TIME ZONE 'UTC';")
            cursor.close()

    def get_all_station_objects(self, typeFilter = None) -> list[StationDbObject]:
        query = text("SELECT \"Id\" FROM \"Stations\";")
        if typeFilter:
            query = (text(f"SELECT \"Id\" FROM \"Stations\" WHERE \"Type\" IN :types;").bindparams(bindparam("types", expanding=True)))
        stations = []
        with self.engine.connect() as connection:
            if typeFilter:
                result = connection.execute(query, {"types":typeFilter}).fetchall()
            else:
                result = connection.execute(query).fetchall()
            for res in result:
                station_id = res[0]
                station = StationDbObject(station_id=station_id)
                station.set_or_update_station_metadata(self.engine)
                stations.append(station)
        return stations
    
    def create_all_stations_data_tables(self):
        stations = self.get_all_station_objects()
        for station in stations:
            if station.Manufacturer == "DeltaOHM":  
                if station.DataSourceId is None:
                    raise ValueError(f"Station {station.Id} does not have a DataSourceId.")
                table_creator = C2aiTableCreator(self.engine, station.DataSourceId)
                table_creator.create_postgre_table()
                dataDf = table_creator.get_data_df()
                self.insert_df(dataDf, table_creator.newTableName)
            if station.Manufacturer == "Pessl":
                table_creator = CfTableCreator(station.Id)
                dataDf = table_creator.getFullStationData()
                self.insert_df(dataDf, station.Id)

    def insert_df(self, df, tableName):
        with self.engine.begin() as connection:
            df.to_sql(
                name=tableName,
                con=connection,
                if_exists="append",
                index=False,
                method="multi",
                chunksize=self.CHUNK_SIZE
            )

    def get_stations_Geojson_object(self, typeFilter = None):
        stations = self.get_all_station_objects(typeFilter)
        geoJson =  GeoJsonObject()
        for st in stations:
            feature = GeoJsonStationInfoFeature(st)
            geoJson.add_feature(feature) # type: ignore
        return geoJson.to_dict()
    
    def update_c2ai_tables(self):
        stations = self.get_all_station_objects()
        for station in stations:
            if station.Manufacturer != "DeltaOHM":
                continue
            if station.DataSourceId is None:
                raise ValueError(f"Station {station.Id} does not have a DataSourceId.")
            table_creator = C2aiTableCreator(self.engine, station.DataSourceId)
            station.set_last_data_point_time(self.engine)
            dataDf = table_creator.get_data_df(int(station.LastDataPointTime.replace(tzinfo=timezone.utc).timestamp())) # type: ignore
            self.insert_df(dataDf, table_creator.newTableName)
                
                


