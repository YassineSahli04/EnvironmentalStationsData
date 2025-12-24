from BackEnd.ClimateFieldStations.API.CfStation import CfStation
from sqlalchemy import text

class CfTableCreator(CfStation):
    def __init__(self, stationId :str) -> None:
        super().__init__(stationId)

    def add_station_to_db(self):
        query = f"INSERT INTO \"Stations\" (\"Id\", \"Name\", \"Manufacturer\", \"Type\", \"Latitude\", \"Longitude\", \"Altitude\", \"DataTableName\") VALUES (:id, :name, :manufacturer, :type, :latitude, :longitude, :altitude, :tablename)"
        with self.engine.connect() as connection: # type: ignore
            connection.execute(
            text(query),
                {
                    "id": self.Id,
                    "name": self.Name,
                    "manufacturer": self.Manufacturer,
                    "type": self.Type,
                    "latitude": self.Latitude,
                    "longitude": self.Longitude,
                    "altitude": self.Altitude,
                    "tablename": self.DataTableName,
                }
            )
            connection.commit()

    
