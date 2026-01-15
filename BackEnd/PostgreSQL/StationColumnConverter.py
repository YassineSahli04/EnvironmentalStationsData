from sqlalchemy import text
import sqlalchemy.engine as _engine
from enum import Enum

class WeatherParamDeltaohmColumns(Enum):
    Temperature= "air_temperature"
    Precipitation= "daily_rainfall"
    Relative_Humidity = "relative_humidity"
    Solar_Radiation = "solar_radiation"
    Wind_Speed = "wind_speed"

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

    @staticmethod
    def build_vpd_expression(temp_col: str, rh_col: str) -> str:
        t = f'"{temp_col}"'
        rh = f'"{rh_col}"'

        raw_expr = (
            f'(1.0 - ({rh} / 100.0)) * 0.6108 * '
            f'EXP((17.27 * {t}) / ({t} + 237.3))'
        )

        return f'ROUND(({raw_expr})::numeric, 1)'

    
    def get_vpd_expression_for_aggr(self, aggr: str) -> str | None:
        try:
            temp_col = self.getActualSensorColumn()
        except (ValueError, NotImplementedError):
            temp_col = None
        if temp_col is None:
            return None

        rh_col = None
        for rh_sensor in ("Relative Humidity", "RH", "Humidity"):
            rh_converter = StationColumnConverter(
                self.engine,
                self.stId,
                self.stManufacturer,
                self.stType,
                rh_sensor,
                aggr,
            )
            try:
                rh_col = rh_converter.getActualSensorColumn()
            except (ValueError, NotImplementedError):
                rh_col = None
            if rh_col is not None:
                break
        if rh_col is None:
            return None

        cols_lower = {c.lower() for c in self.tableColumns}
        if temp_col.lower() not in cols_lower or rh_col.lower() not in cols_lower:
            return None

        return StationColumnConverter.build_vpd_expression(temp_col, rh_col)
