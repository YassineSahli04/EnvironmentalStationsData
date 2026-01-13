from __future__ import annotations
import pandas as pd
from sqlalchemy import text
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from BackEnd.PostgreSQL.StationDbObject import StationDbObject
from BackEnd.PostgreSQL.StationColumnConverter import StationColumnConverter
from enum import Enum
import sqlalchemy.engine as _engine
from dataclasses import dataclass
from datetime import datetime, timezone

class WeatherParamAggregation(Enum):
    Temperature= ["avg","min","max"]
    Precipitation= ["sum"]
    Relative_Humidity= ["avg","min","max"]
    Solar_Radiation= ["sum"]
    Wind_Speed= ["avg","min","max"]

    @staticmethod
    def weatherParamToEnumKey(weatherParam):
        return weatherParam.strip().replace(" ", "_")



@dataclass
class SensorSerializable:
    stationId: str
    sensor: str
    # unit: str    The UNITs are not got yet from the api, This will be added later
    aggregationsType: list
    data: pd.DataFrame | list


class SensorDbObject:
    engine: _engine.Engine
    station: StationDbObject;
    sensor: str;
    aggr: list;
    columnNames: dict
    def __init__(self, station: StationDbObject, sensor :str, isDataInDf = True) -> None:
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
            converter = StationColumnConverter(self.engine, self.station.Id,self.station.Manufacturer, self.station.Type, self.sensor, elem)
            col = converter.getActualSensorColumn()
            if col is not None:
                self.columnNames[elem] = col


    def getSensorAllDataColumns(self, dataGroup:str, startDtUTC :datetime, endDtUTC:datetime):
        if len(self.columnNames) == 0:
            raise ValueError(f"{self.sensor} Sensor data not available for Station {self.station.Id}.")
    
        aggSelects = ",\n".join([f'{elem}("{self.columnNames[elem]}") AS "{elem}"' for elem in self.columnNames])

        df = SensorDbObject.getdfFromQueryResult(self.engine, self.station.Id, aggSelects, dataGroup, startDtUTC, endDtUTC)
        
        if self.isDataInDf:
            return df
        
        lastSensorData = self.getLastSensorData()
        return SensorDbObject.dfToTimeValueRecords(df, self.aggr, startDtUTC, lastSensorData)
    
    @staticmethod
    def dfToTimeValueRecords(
        df: pd.DataFrame,
        cols: list[str],
        startDtUTC: datetime,
        lastSensorData: float | None = None,
        dateTimeCol: str = "Date/Time",
        lastMeasuredKey: str = "last measured",
    ) -> list[dict]:
        records: list[dict] = []

        nowUTC = datetime.now(timezone.utc)
        is_today_utc = startDtUTC.date() == nowUTC.date()

        for _, row in df.iterrows():
            values = {a: row[a] for a in cols}

            if is_today_utc and lastMeasuredKey is not None:
                values[lastMeasuredKey] = lastSensorData

            t = row[dateTimeCol]
            if hasattr(t, "to_pydatetime"):
                t = t.to_pydatetime()

            records.append({"time": t, "values": values})
        return records

    def getDefaultSensorColumn(self):
        if len(self.columnNames) == 0:
            raise ValueError(f"{self.sensor} Sensor data not available for Station {self.station.Id}.")
        if len(self.columnNames) == 1 :
            (key,col), = self.columnNames.items()
        if len(self.columnNames) > 1:
            key = 'avg'
            col = self.columnNames['avg']
        return key, col   

    @staticmethod
    def getdfFromQueryResult(engine: _engine.Engine, table: str, aggSelects: str, dataGroup:str, startDtUTC :datetime, endDtUTC:datetime):
        sql = text(f"""
                SELECT
                    date_trunc(:step, "date_time") AS "Date/Time",
                    {aggSelects}
                FROM "{table}"
                WHERE "date_time" >= :start_dt
                AND "date_time" <  :end_dt
                GROUP BY "Date/Time"
                ORDER BY "Date/Time";
            """)

        queryParams = {
            "step": dataGroup,
            "start_dt": startDtUTC,
            "end_dt": endDtUTC, 
        }
        with engine.connect() as connection:
            return pd.read_sql(sql, connection, params=queryParams)

    def getLastSensorData(self):
        if ("avg" in self.columnNames):
            col = self.columnNames["avg"]
        elif ("sum" in self.columnNames):
            col = self.columnNames["sum"]
        else:
            raise Exception(f"Columns ({self.columnNames}) Not handeled for Last Sensor Data")
        
        query = text(f"""
                SELECT "{col}"
                FROM "{self.station.Id}"
                WHERE "{col}" IS NOT NULL
                ORDER BY "date_time" DESC
                LIMIT 1;
            """)
        with self.engine.connect() as connection:
            results = connection.execute(query).fetchall()
            vals = [r[0] for r in results]
        return vals[0]

    def getSerializableObj(self, data) -> SensorSerializable:
        return SensorSerializable(
            stationId = self.station.Id,
            sensor = self.sensor,
            aggregationsType = self.aggr,
            data= data
        )