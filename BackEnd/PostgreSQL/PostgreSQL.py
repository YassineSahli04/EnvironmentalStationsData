import json
import sqlalchemy.engine as _engine
from sqlalchemy import create_engine, text
from pathlib import Path
from BackEnd.PostgreSQL.StationDbObject import StationDbObject
from BackEnd.C2aiStations.TableCreator import TableCreator

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

    def get_all_station_objects(self) -> list[StationDbObject]:
        query = text("SELECT \"Id\" FROM \"Stations\";")
        stations = []
        with self.engine.connect() as connection:
            result = connection.execute(query).fetchall()
            for res in result:
                station_id = res[0]
                station = StationDbObject(engine=self.engine, station_id=station_id)
                station.set_or_update_station_data()
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
                
           
