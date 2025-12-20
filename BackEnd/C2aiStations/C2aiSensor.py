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
AVAILABLE_AGGREGATION = {
    "Temperature": ["avg","min","max"],
    "Precipitation": ["sum"],
    "Relative Humidity": ["avg","min","max"],
    "Solar Radiation": ["sum"],
    "Wind Speed": ["avg","min","max"],
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
        aggregationTypes = AVAILABLE_AGGREGATION[self.sensorId]
            
        aggSelects = ",\n".join([f'{a}("{column_name}") AS "{a}"' for a in aggregationTypes])

        if(self.sensorId == "Precipitation"): 
            sql = self.getPrecipitationSensorQuery(column_name, aggregationTypes)
        else: 
            sql = text(f"""
                SELECT
                    date_trunc(:step, "date_time") AS "Date/Time",
                    {aggSelects}
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
            values = {agg: row[agg] for agg in aggregationTypes}
            records.append({
                "time": row["Date/Time"],
                "values": values
            })

        if(self.stationId == "ed_8441-ed_8539"): print(records)

        self.data = records

    def getPrecipitationSensorQuery(self, column_name, aggregationTypes):
        aggSelects = ",\n".join([f'"{column_name}" AS "{a}"' for a in aggregationTypes])

        x = text(f"""
            SELECT
                "date_time" AS "Date/Time",
                {aggSelects}                
            FROM "{self.stationId}"
            WHERE "date_time" >= :start_dt
            AND "date_time" <  :end_dt
            AND "{column_name}" IS NOT NULL
            ORDER BY "Date/Time"
            DESC LIMIT 1;
        """)
        if(self.stationId == "ed_8441-ed_8539"):print(x)
        return x
    


