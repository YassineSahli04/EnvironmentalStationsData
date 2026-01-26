from __future__ import annotations
import pandas as pd
from sqlalchemy import text
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from BackEnd.PostgreSQL.StationDbObject import StationDbObject
import sqlalchemy.engine as _engine
from dataclasses import dataclass
from datetime import datetime, timezone

@dataclass
class SensorSerializable:
    stationId: str
    sensor: str
    unit: str
    aggregationsType: list
    data: list | None


class SensorDbObject:
    engine: _engine.Engine
    station: StationDbObject;
    sensor: str;
    aggregationsType: set;
    unit: str;
    columnNames: dict
    def __init__(self, station: StationDbObject, sensor :str, isDataInDf = True) -> None:
        self.engine = station.engine
        self.isDataInDf = isDataInDf
        self.sensor = sensor.lower()
        self.station = station
        self.setColumnsMetadata()


    def getSensorAllDataColumns(self, dataGroup:str, startDtUTC :datetime, endDtUTC:datetime):
        if len(self.columnNames) == 0:
            raise ValueError(f"{self.sensor} Sensor data not available for Station {self.station.Id}.")
    
        aggSelects = ",\n".join([f'{elem}("{self.columnNames[elem]}") AS "{elem}"' for elem in self.columnNames])

        df = SensorDbObject.getdfFromQueryResult(self.engine, self.station.Id, aggSelects, dataGroup, startDtUTC, endDtUTC)
        
        if self.isDataInDf:
            return df
        
        lastSensorDt, lastSensorData = self.getLastSensorData()
        return SensorDbObject.dfToTimeValueRecords(df, self.aggregationsType, startDtUTC, lastSensorData)
    
    @staticmethod
    def dfToTimeValueRecords(
        df: pd.DataFrame,
        cols: list[str] | set,
        startDtUTC: datetime,
        lastSensorData: float | None = None,
        dateTimeCol: str = "Date/Time",
        lastMeasuredKey: str = "last measured",
    ) -> list[dict]:
        records: list[dict] = []

        nowUTC = datetime.now(timezone.utc)
        is_today_utc = startDtUTC.date() == nowUTC.date()

        for _, row in df.iterrows():
            values = {a: (None if pd.isna(row[a]) else row[a]) for a in cols}

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
                SELECT "date_time", "{col}"
                FROM "{self.station.Id}"
                WHERE "{col}" IS NOT NULL
                ORDER BY "date_time" DESC
                LIMIT 1;
            """)
        with self.engine.connect() as connection:
            results = connection.execute(query).fetchone()
        if results is None:
            return None, None
        return results[0], results[1]
    
    def setColumnsMetadata(self):
        query = text(f"""
            SELECT "column_name", "unit", "aggregation"
            FROM "StationColumn"
            WHERE "station_id" = '{self.station.Id}'
            AND "param" = '{self.sensor}'
        """)
        with self.engine.begin() as conn:
            res = conn.execute(query).fetchall()
        if len(res) == 0:
            raise ValueError(f"{self.sensor} Sensor data not available for Station {self.station.Id}.") 
        self.aggregationsType = set()
        self.columnNames = {}
        for colRow in res:
            colName, unit, aggrList = colRow
            if aggrList is None:
                self.aggregationsType.add('avg')
                self.columnNames['avg'] = colName
                continue
            for aggr in aggrList:
                self.aggregationsType.add(aggr)
                self.columnNames[aggr] = colName
        self.unit = unit
    
    def getSerializableObj(self, data:  list | None) -> SensorSerializable:
        return SensorSerializable(
            stationId = self.station.Id,
            sensor = self.sensor,
            aggregationsType = list(self.aggregationsType),
            unit=self.unit,
            data= data
        )

