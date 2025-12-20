from logging import exception
from BackEnd.ClimateFieldStations.TransformData import TransformData
import pandas as pd
from sqlalchemy import text, bindparam
from BackEnd.C2aiStations.C2aiApi.C2aiStationsApiCalls import C2aiStationsApiCalls
from BackEnd.C2aiStations.C2aiApi.QueryObject import QueryObject 
from pathlib import Path
import sqlalchemy.engine as _engine
from enum import Enum

class TableType(Enum):
    AlimentationTable= "AlimentationTable"
    MeteoTable = "MeteoTable"
    PluviometerTable = "PluviometerTable"
    MicroClimateTable = "MicroClimateTable"

class TableColumnNameTransformer:
    MEAS_RENAME_BY_TYPE = {
        "AlimentationTable": {
            "MEAS_1": "battery_voltage_v",
            "MEAS_2": "supply_voltage_v",
        },
        "MeteoTable": {
            "MEAS_1": "wind_speed_ms",
            "MEAS_2": "wind_direction_deg",
            "MEAS_3": "air_temperature_c",
            "MEAS_4": "relative_humidity_pct",
            "MEAS_5": "dew_point_c",
            "MEAS_6": "solar_radiation_w_m2",
            "MEAS_7": "atmospheric_pressure_hpa",
            "MEAS_8": "hourly_evapotranspiration_mm_h",
            "MEAS_9": "daily_evapotranspiration_mm_d",
        },
        "PluviometerTable": {
            "MEAS_1": "rain_intensity_mm_h",
            "MEAS_2": "daily_rainfall_mm",
            "MEAS_3": "total_rainfall_mm",
        },
        "MicroClimateTable": {
            "MEAS_1": "microclimate_temperature_c",
            "MEAS_2": "microclimate_relative_humidity_pct",
            "MEAS_3": "microclimate_dew_point_c",
            "MEAS_4": "microclimate_absolute_humidity_g_m3",
            "MEAS_5": "microclimate_upper_leaf_wetness_pct",
            "MEAS_6": "microclimate_lower_leaf_wetness_pct",
        },
    }


class C2aiTableCreator:
    CHUNK_SIZE = 5000
    SECRETJSONPATH = Path(__file__).resolve().parents[2] / "BackEnd/PostgreSQL/DbInfo.json"
    newTableName: str | None;
    mysql_ddl: str;
    sourceDataId: int;
    engine: _engine.Engine;
    oldTableName :str;
    edTablesDict: dict;
    def __init__(self, engine, sourceDataId):
        self.sourceDataId = sourceDataId
        self.oldTableName = "ed"
        self.set_ed_tables_type_and_new_table_name()
        self.engine = engine
        
    def set_ed_tables_type_and_new_table_name(self):
        firstNamePart = ""
        secondNamePart = ""
        edTablesList = self.set_ed_tables_list()
        dict = {}
        for table in edTablesList:
            tableType =self.get_c2ai_table_type(table)
            if tableType is None:
                continue
            dict[table] = tableType
            if tableType == TableType.MeteoTable:
                firstNamePart = str(table)
            if tableType == TableType.PluviometerTable:
                secondNamePart = str(table)
        self.edTablesDict = dict
        self.newTableName = firstNamePart + '-' + secondNamePart

    def set_ed_tables_list(self):
        query = f"SELECT table_name FROM information_schema.tables WHERE table_name LIKE '%ed%' and table_schema = DATABASE();"
        queryObject = QueryObject(self.sourceDataId, query)
        apiCall = C2aiStationsApiCalls([queryObject])
        jsonResponse = apiCall.getRawResponse()
        return list(jsonResponse.get("results").get(queryObject.refId).get('frames')[0].get('data').get('values')[0])  # type: ignore

    def fix_datetime(self, col: pd.Series) -> pd.Series:
        return pd.to_datetime(col, unit="ms", origin="unix", errors="coerce")
    
    def fix_number(self, col: pd.Series) -> pd.Series:
        return pd.to_numeric(col, errors="coerce")
    
    def transform_df(self, df: pd.DataFrame, table_type) -> pd.DataFrame:
        new_df = df.copy()
        meas_map = TableColumnNameTransformer.MEAS_RENAME_BY_TYPE.get(table_type.value, {})

        for col in new_df.columns:
            clean_name = col.split(" : ")[0]

            if clean_name == "DATE_TIME":
                new_df[col] = self.fix_datetime(new_df[col])
            elif clean_name.startswith("MEAS_"):
                new_df[col] = self.fix_number(new_df[col])

        final_cols = []
        kept_cols = []

        for col in new_df.columns:
            clean_name = col.split(" : ")[0]

            if clean_name == "DATE_TIME":
                final_cols.append("date_time")
                kept_cols.append(col)

            elif clean_name in meas_map:
                final_cols.append(meas_map[clean_name])
                kept_cols.append(col)

        new_df = new_df[kept_cols]
        new_df.columns = final_cols

        return new_df
    
    def insert_df(self, df):
        with self.engine.begin() as connection:
            df.to_sql(
                name=self.newTableName,
                con=connection,
                if_exists="append",
                index=False,
                method="multi",
                chunksize=self.CHUNK_SIZE
            )
    
    def get_c2ai_table_type(self, tableName: str):
        query = f"SELECT (CASE WHEN SUM(CASE WHEN MEAS_1 <> 0 THEN 1 ELSE 0 END) > 0 THEN 1 ELSE 0 END + CASE WHEN SUM(CASE WHEN MEAS_2 <> 0 THEN 1 ELSE 0 END) > 0 THEN 1 ELSE 0 END + CASE WHEN SUM(CASE WHEN MEAS_3 <> 0 THEN 1 ELSE 0 END) > 0 THEN 1 ELSE 0 END + CASE WHEN SUM(CASE WHEN MEAS_4 <> 0 THEN 1 ELSE 0 END) > 0 THEN 1 ELSE 0 END + CASE WHEN SUM(CASE WHEN MEAS_5 <> 0 THEN 1 ELSE 0 END) > 0 THEN 1 ELSE 0 END + CASE WHEN SUM(CASE WHEN MEAS_6 <> 0 THEN 1 ELSE 0 END) > 0 THEN 1 ELSE 0 END + CASE WHEN SUM(CASE WHEN MEAS_7 <> 0 THEN 1 ELSE 0 END) > 0 THEN 1 ELSE 0 END + CASE WHEN SUM(CASE WHEN MEAS_8 <> 0 THEN 1 ELSE 0 END) > 0 THEN 1 ELSE 0 END + CASE WHEN SUM(CASE WHEN MEAS_9 <> 0 THEN 1 ELSE 0 END) > 0 THEN 1 ELSE 0 END + CASE WHEN SUM(CASE WHEN MEAS_10 <> 0 THEN 1 ELSE 0 END) > 0 THEN 1 ELSE 0 END + CASE WHEN SUM(CASE WHEN MEAS_11 <> 0 THEN 1 ELSE 0 END) > 0 THEN 1 ELSE 0 END + CASE WHEN SUM(CASE WHEN MEAS_12 <> 0 THEN 1 ELSE 0 END) > 0 THEN 1 ELSE 0 END) AS non_zero_meas_columns FROM {tableName}"
        queryObject = QueryObject(self.sourceDataId, query)
        apiCall = C2aiStationsApiCalls([queryObject])
        jsonResponse = apiCall.getRawResponse()
        fullColumnsNumber = int(jsonResponse.get("results").get(queryObject.refId).get('frames')[0].get('data').get('values')[0][0])  # type: ignore
        if fullColumnsNumber == 2:
            return TableType.AlimentationTable
        elif fullColumnsNumber == 3:
            return TableType.PluviometerTable
        elif fullColumnsNumber == 6:
            return TableType.MicroClimateTable
        elif fullColumnsNumber >= 7 and fullColumnsNumber <= 9:
            return TableType.MeteoTable
        else:
            return None
        
    def create_postgre_table(self):
        query = f"CREATE TABLE \"{self.newTableName}\" (date_time TIMESTAMPTZ PRIMARY KEY, battery_voltage_v NUMERIC(10,3), supply_voltage_v NUMERIC(10,3), wind_speed_ms NUMERIC(10,3), wind_direction_deg NUMERIC(10,3), air_temperature_c NUMERIC(10,3), relative_humidity_pct NUMERIC(10,3), dew_point_c NUMERIC(10,3), solar_radiation_w_m2 NUMERIC(10,3), atmospheric_pressure_hpa NUMERIC(10,3), hourly_evapotranspiration_mm_h NUMERIC(10,3), daily_evapotranspiration_mm_d NUMERIC(10,3), rain_intensity_mm_h NUMERIC(10,3), daily_rainfall_mm NUMERIC(10,3), total_rainfall_mm NUMERIC(10,3), microclimate_temperature_c NUMERIC(10,3), microclimate_relative_humidity_pct NUMERIC(10,3), microclimate_dew_point_c NUMERIC(10,3), microclimate_absolute_humidity_g_m3 NUMERIC(10,3), microclimate_upper_leaf_wetness_pct NUMERIC(10,3), microclimate_lower_leaf_wetness_pct NUMERIC(10,3));"
        with self.engine.connect() as connection:
            connection.execute(text(query))
            connection.commit()
    
    def get_highest_starting_timestamp(self):
        highestTime = 0
        for table in self.edTablesDict:
            query = f"SELECT MIN(DATE_TIME) AS oldest_time FROM {table};"
            queryObject = QueryObject(self.sourceDataId, query)
            apiCall = C2aiStationsApiCalls([queryObject])
            jsonResponse = apiCall.getRawResponse()
            time = int(jsonResponse.get("results").get(queryObject.refId).get('frames')[0].get('data').get('values')[0][0]) # type: ignore
            if time > highestTime: 
                highestTime = time
        return highestTime // 1000

    def get_table_data(self, table, unixStartTime):
        columnsList = self.get_table_used_columns(table)

        cols_sql = ", ".join(columnsList)
        query =  (
            f"SELECT {cols_sql} "
            f"FROM {table} "
            f"WHERE DATE_TIME > FROM_UNIXTIME({unixStartTime});"
        )
        queryObject = QueryObject(self.sourceDataId, query)
        apiCall = C2aiStationsApiCalls([queryObject])
        for df in apiCall.getResponse():
            return self.transform_df(df, self.edTablesDict[table])

    def get_table_used_columns(self, table) -> list:
        if self.edTablesDict[table] == TableType.AlimentationTable:
            return ["DATE_TIME", "MEAS_1", "MEAS_2"]
        elif self.edTablesDict[table] == TableType.PluviometerTable:
            return ["DATE_TIME", "MEAS_1", "MEAS_2", "MEAS_3"]
        elif self.edTablesDict[table] == TableType.MicroClimateTable:
            return ["DATE_TIME", "MEAS_1", "MEAS_2", "MEAS_3", "MEAS_4", "MEAS_5", "MEAS_6"]
        else:
            return ["DATE_TIME", "MEAS_1", "MEAS_2", "MEAS_3", "MEAS_4", "MEAS_5", "MEAS_6", "MEAS_7", "MEAS_8", "MEAS_9"]

    def get_data_and_insert(self, unixStartTime = None):
        dfList = []
        if unixStartTime is None: unixStartTime = self.get_highest_starting_timestamp()
        for table in self.edTablesDict:
            dfList.append(self.get_table_data(table, unixStartTime))
        combinedData =  TransformData.combine_dfs_with_diff_timestamp(dfList, "date_time")
        self.insert_df(combinedData)
