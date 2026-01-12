from sqlalchemy import text
import sqlalchemy.engine as _engine
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
    def __init__(self,engine: _engine.Engine, stId: str, stManufacturer: str | None, stType: str | None, sensor:str, aggr: str):
        self.engine = engine
        self.stId = stId
        self.stManufacturer = stManufacturer
        self.stType = stType
        self.searchedTableColumn = sensor
        self.aggr = aggr
        self.tableColumns = StationColumnConverter.getStationTableAvailableColumns(engine, self.stId)
        

    @staticmethod
    def getStationTableAvailableColumns(engine: _engine.Engine, stId: str):
        query = text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'public'
            AND table_name = :tableName
            ORDER BY ordinal_position;
        """)
        with engine.connect() as connection:
            results = connection.execute(query, {"tableName": stId})
        return [res[0] for res in results]

    def getActualSensorColumn(self):
        column = None
        match self.stManufacturer:
            case "DeltaOHM":
                weatherParamKey = WeatherParamDeltaohmColumns.weatherParamToEnumKey(self.searchedTableColumn)
                try:
                    column = WeatherParamDeltaohmColumns[weatherParamKey].value
                except KeyError:
                    allowed = [e.name.replace("_", " ") for e in WeatherParamDeltaohmColumns]
                    raise ValueError(f"Invalid Sensor '{self.searchedTableColumn}'. Allowed: {allowed}")
            case "Pessl":
                if self.stType == 'Aquachek' or self.stType == 'Drill and Drop':
                    raise NotImplementedError(f"Station {self.stId} is of type {self.stType} and code hasn't been implemented yet for that type.")
                sensor = self.searchedTableColumn.strip().lower()
                aggr = self.aggr.strip().lower()
                
                sensorMatch = []
                for col in self.tableColumns:
                    if sensor in col.lower():
                        if aggr in col.lower():
                            column = col
                            break
                        sensorMatch.append(col)
                        
                if column is None and len(sensorMatch) == 1:
                    column = sensorMatch[0]

            case _:
                raise Exception("Data Tables are only available for DeltaOHM Stations and Pessl")
            
        return column
    
