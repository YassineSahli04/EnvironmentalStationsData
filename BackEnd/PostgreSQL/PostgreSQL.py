import json
import sqlalchemy.engine as _engine
from sqlalchemy import create_engine, text, bindparam
import os
from BackEnd.GeoJson.GeoJsonStationInfoFeature import GeoJsonStationInfoFeature
from BackEnd.PostgreSQL.StationDbObject import StationDbObject
from BackEnd.C2aiStations.Api.C2aiTableCreator import C2aiTableCreator
from BackEnd.GeoJson.GeoJsonObject import GeoJsonObject
from BackEnd.ClimateFieldStations.API.CfTableCreator import CfTableCreator
from concurrent.futures import ThreadPoolExecutor

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
                station = StationDbObject(self.engine, station_id)
                stations.append(station)
        return stations
    
    def create_update_all_stations_data_tables(self):
        stations = self.get_all_station_objects()
        for station in stations:
            match station.Manufacturer:
                case "DeltaOHM":
                    if station.DataSourceId is None:
                        raise ValueError(f"Station {station.Id} does not have a DataSourceId.")
                    table_creator = C2aiTableCreator(self.engine, station.DataSourceId)
                    alreadyExists = table_creator.create_postgre_table()
                    
                case "Pessl":
                    table_creator = CfTableCreator(self.engine, station.Id)
                    alreadyExists = table_creator.IsDataTableCreated()

            if not alreadyExists:
                dataDf = table_creator.getFullDataDf()
                self.insert_create_data_df(dataDf, table_creator.newTableName)
            else:
                self.update_db_table(station)

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

    def create_station_column_table(self):
        query = text("""
            CREATE TABLE IF NOT EXISTS "StationColumn" (
                "id"              BIGSERIAL PRIMARY KEY,

                "station_id"      TEXT NOT NULL
                                REFERENCES "Stations"("Id")
                                ON DELETE CASCADE,
                     
                "column_name"     TEXT NOT NULL,

                "data_type"       TEXT NOT NULL,
                "unit"            TEXT NULL,
                "aggregation" TEXT[],

                "param" TEXT NULL,
                "confidence"      DOUBLE PRECISION NULL CHECK ("confidence" IS NULL OR ("confidence" >= 0 AND "confidence" <= 1)),

                "source"          TEXT NOT NULL CHECK (source IN (
                                    'inferred',
                                    'manufacturer_template',
                                    'manual'
                                )),

                "updated_at"      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

                CONSTRAINT uq_station_column UNIQUE ("station_id", "column_name")
            );

        """)

        with self.engine.begin() as connection:
            connection.execute(query)
        
    def get_stations_Geojson_object(self, typeFilter = None):
        stations = self.get_all_station_objects(typeFilter)

        with ThreadPoolExecutor(max_workers=8) as ex:
            features = list(ex.map(GeoJsonStationInfoFeature, stations))

        geoJson =  GeoJsonObject()
        for feature in features:
            geoJson.add_feature(feature) # type: ignore
        return geoJson.to_dict()

    def update_db_table(self, station: StationDbObject):
        match station.Manufacturer:
            case "DeltaOHM":
                if station.DataSourceId is None:
                    raise ValueError(f"DeltaOHM Station {station.Id} does not have a DataSourceId.")
                table_creator = C2aiTableCreator(self.engine, station.DataSourceId)
            case "Pessl":
                table_creator = CfTableCreator(self.engine, station.Id)
            case _:
                raise Exception("Data Tables are only available for DeltaOHM Stations and Pessl")
        dataDf = table_creator.getFullDataDf(station.LastDataPointTime) # type: ignore
        self.insert_create_data_df(dataDf, table_creator.newTableName)