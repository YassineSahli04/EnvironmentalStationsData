import pandas as pd
from sqlalchemy import text
from BackEnd.PostgreSQL.StationColumnConverter import StationColumnConverter
from BackEnd.PostgreSQL.StationDbObject import StationDbObject
from enum import Enum
import sqlalchemy.engine as _engine

class WeatherParamAggregation(Enum):
    Temperature= ["avg","min","max"]
    Precipitation= ["sum"]
    Relative_Humidity= ["avg","min","max"]
    Solar_Radiation= ["sum"]
    Wind_Speed= ["avg","min","max"]

    @staticmethod
    def weatherParamToEnumKey(weatherParam):
        return weatherParam.strip().replace(" ", "_")


class SensorDbObject:
    engine: _engine.Engine
    station: StationDbObject;
    sensor: str;
    aggr: list;
    data: pd.DataFrame | list;
    columnNames: dict
    def __init__(self, station: StationDbObject, sensor, isDataInDf = True) -> None:
        self.engine = station.engine
        self.isDataInDf = isDataInDf
        self.sensor = sensor
        self.station = station
        self.setAggr()
        self.setColumns()

    def setAggr(self):
        try:
            weatherParamKey = WeatherParamAggregation.weatherParamToEnumKey(self.sensor)
            self.aggr = WeatherParamAggregation[weatherParamKey].value
        except KeyError:
            allowed = [e.name.replace("_", " ") for e in WeatherParamAggregation]
            raise ValueError(f"Invalid Sensor '{self.sensor}'. Allowed: {allowed}")
        
    def setColumns(self):
        if self.aggr is None:
            raise ValueError(f"Aggregation is not set.")
        self.columnNames = {}
        for elem in self.aggr:
            converter = StationColumnConverter(self.station, self.sensor, elem)
            self.columnNames[elem] = converter.getActualSensorColumn()


    def setSensorData(self, queryParams):  
        aggSelects = ",\n".join([f'{elem}("{self.columnNames[elem]}") AS "{elem}"' for elem in self.columnNames])

        if(self.sensor == "Precipitation" and self.station.Manufacturer == "DeltaOHM"): 
            sql = self.getC2aiPrecipitationSensorQuery()
        else: 
            sql = text(f"""
                SELECT
                    date_trunc(:step, "date_time") AS "Date/Time",
                    {aggSelects}
                FROM "{self.station.Id}"
                WHERE "date_time" >= :start_dt
                AND "date_time" <  :end_dt
                GROUP BY "Date/Time"
                ORDER BY "Date/Time";
            """)


        with self.engine.connect() as connection:
            df = pd.read_sql(sql, connection, params=queryParams)

        if self.isDataInDf:
            self.data = df
            return

        records = []
        for _, row in df.iterrows():
            values = {agg: row[agg] for agg in self.aggr}
            records.append({
                "time": row["Date/Time"],
                "values": values
            })

        self.data = records

    def getC2aiPrecipitationSensorQuery(self):
        colName = self.columnNames['sum']
        aggSelects = ",\n".join([f'"{colName}" AS "{elem}"' for elem in self.columnNames])

        return text(f"""
            SELECT
                "date_time" AS "Date/Time",
                {aggSelects}                
            FROM "{self.station.Id}"
            WHERE "date_time" >= :start_dt
            AND "date_time" <  :end_dt
            AND "{colName}" IS NOT NULL
            ORDER BY "Date/Time"
            DESC LIMIT 1;
        """)