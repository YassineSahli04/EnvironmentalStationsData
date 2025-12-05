import pandas as pd
from BackEnd.PostgreSQL.StationDbObject import StationDataGroup
import sqlalchemy.engine as _engine
from sqlalchemy import text

granularityMap = {
    StationDataGroup.hourly: 'hour',
    StationDataGroup.daily: 'day',
    StationDataGroup.monthly: 'month'
}
PARAM_TO_COLUMN_DELTAOHM = {
    "Temperature": "air_temperature_c",
    "Precipitation": "daily_rainfall_mm",
    "Relative Humidity": "relative_humidity_pct",
    "Solar Radiation": "solar_radiation_w_m2",
    "Wind Speed": "wind_speed_ms",
}

class C2aiSensor:
    stationId: str;
    sensorId: str;
    data: pd.DataFrame | list;
    def __init__(self, stationId, sensorId, isDataInDf = True) -> None:
        self.stationId = stationId
        self.isDataInDf = isDataInDf
        self.sensorId = sensorId

    def setSensorData(self, engine, queryParams):
        column_name = PARAM_TO_COLUMN_DELTAOHM[self.sensorId]

        sql = text(f"""
            SELECT
                date_trunc(:step, "date_time") AS "Date/Time",
                avg("{column_name}") AS "{self.sensorId}"
            FROM "{self.stationId}"
            WHERE "date_time" >= :start_dt
            AND "date_time" <  :end_dt
            GROUP BY "Date/Time"
            ORDER BY "Date/Time";
        """)


        with engine.connect() as connection:
            df = pd.read_sql(sql, connection, params=queryParams)

        if self.isDataInDf:
            self.data = df
            return

        records = []
        for _, row in df.iterrows():
            values = {"avg": row[self.sensorId]}
            records.append({
                "time": row["Date/Time"],
                "values": values
            })

        self.data = records