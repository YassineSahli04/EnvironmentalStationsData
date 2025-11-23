import json
import sqlalchemy.engine as _engine
from sqlalchemy import create_engine, text, bindparam
from pathlib import Path
from BackEnd.GeoJson.GeoJsonStationInfoFeature import GeoJsonStationInfoFeature
from BackEnd.PostgreSQL.StationDbObject import StationDbObject
from BackEnd.C2aiStations.C2aiTableCreator import TableCreator
from BackEnd.GeoJson.GeoJsonObject import GeoJsonObject

class PostgreSQL:
    SECRETJSONPATH = Path(__file__).resolve().parents[2] / "BackEnd/PostgreSQL/DbInfo.json"
    engine: _engine.Engine;
    def __init__(self):
        self.initialize_postgres_connection()
        

    def initialize_postgres_connection(self):
        with open(self.SECRETJSONPATH, "r") as f:
            data = json.load(f)
            
        userName = data.get("userName")
        password = data.get("password")
        host = data.get("host")
        port = data.get("port")
        database = data.get("database")

        connection_string = f"postgresql+psycopg2://{userName}:{password}@{host}:{port}/{database}"

        self.engine = create_engine(connection_string)

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
                station.set_or_update_station_data(self.engine)
                stations.append(station)
        return stations
    
    def create_all_c2ai_stations_data_tables(self):
        stations = self.get_all_station_objects()
        for station in stations:
            if station.Manufacturer != "DeltaOHM":
                continue
            if station.DataSourceId is None:
                raise ValueError(f"Station {station.Id} does not have a DataSourceId.")
            table_creator = TableCreator(self.engine, station.DataSourceId, station.Id)
            table_creator.create_postgre_table()
            table_creator.get_all_data_and_insert()

    def get_stations_Geojson_object(self, typeFilter = None):
        stations = self.get_all_station_objects(typeFilter)
        geoJson =  GeoJsonObject()
        for st in stations:
            feature = GeoJsonStationInfoFeature(st)
            geoJson.add_feature(feature) # type: ignore
        return geoJson.to_dict()


                
           
