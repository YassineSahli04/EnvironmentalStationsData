from sqlalchemy import text
import sqlalchemy.engine as _engine
from BackEnd.PostgreSQL.StationDbObject import StationDbObject
from enum import Enum

class WeatherParamDeltaohmColumns(Enum):
    Temperature= "air_temperature_c"
    Precipitation= "daily_rainfall_mm"
    Relative_Humidity = "relative_humidity_pct"
    Solar_Radiation = "solar_radiation_w_m2"
    Wind_Speed = "wind_speed_ms"

    @staticmethod
    def weatherParamToEnumKey(weatherParam):
        return weatherParam.strip().replace(" ", "_")


class StationColumnConverter:
    def __init__(self, station:StationDbObject, sensor:str, aggr: str):
        self.station = station
        self.searchedTableColumn = sensor
        self.aggr = aggr
        self.setStationTableAvailableColumns()
        

    def setStationTableAvailableColumns(self):
        query = text("SELECT column_name FROM information.schema.columns WHERE table_schema = 'public' AND table_name = :tableName ORDER BY ordinal_position;")
        with self.station.engine.connect() as connection:
            results = connection.execute(query, {"tableName": self.station.Id})
        self.tableColumns = [res[0] for res in results]

    def getActualSensorColumn(self):
        column = ''
        match self.station.Manufacturer:
            case "DeltaOHM":
                weatherParamKey = WeatherParamDeltaohmColumns.weatherParamToEnumKey(self.searchedTableColumn)
                try:
                    column = WeatherParamDeltaohmColumns[weatherParamKey].value
                except KeyError:
                    allowed = [e.name.replace("_", " ") for e in WeatherParamDeltaohmColumns]
                    raise ValueError(f"Invalid Sensor '{self.searchedTableColumn}'. Allowed: {allowed}")
                return 
            case "Pessl":
                if self.station.Type == 'Aquachek' or self.station.Type == 'Drill and Drop':
                    raise NotImplementedError(f"Station {self.station.Id} is of type {self.station.Type} and code hasn't been implemented yet for that type.")
                sensor = self.searchedTableColumn.strip().lower()
                aggr = self.aggr.strip().lower()
                for col in self.tableColumns:
                    if sensor in col.lower() and aggr in col.lower():
                        column = col
                        break
            case _:
                raise Exception("Data Tables are only available for DeltaOHM Stations and Pessl")
            
        return column
    
