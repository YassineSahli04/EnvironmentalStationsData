from datetime import datetime
from BackEnd.Utils.TransformData import TransformData
import pandas as pd
from sqlalchemy import text
from BackEnd.C2aiStations.Api.C2aiStationsApiCalls import C2aiStationsApiCalls
from BackEnd.C2aiStations.Api.QueryObject import QueryObject 
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
            "MEAS_1": "battery_voltage",
            "MEAS_2": "supply_voltage",
        },
        "MeteoTable": {
            "MEAS_1": "wind_speed",
            "MEAS_2": "wind_direction",
            "MEAS_3": "air_temperature",
            "MEAS_4": "relative_humidity",
            "MEAS_5": "dew_point",
            "MEAS_6": "solar_radiation",
            "MEAS_7": "atmospheric_pressure",
            "MEAS_8": "hourly_evapotranspiration",
            "MEAS_9": "daily_evapotranspiration",
        },
        "PluviometerTable": {
            "MEAS_1": "rain_intensity",
            "MEAS_2": "daily_rainfall",
            "MEAS_3": "total_rainfall",
        },
        "MicroClimateTable": {
            "MEAS_1": "microclimate_temperature",
            "MEAS_2": "microclimate_relative_humidity",
            "MEAS_3": "microclimate_dew_point",
            "MEAS_4": "microclimate_absolute_humidity",
            "MEAS_5": "microclimate_upper_leaf_wetness",
            "MEAS_6": "microclimate_lower_leaf_wetness",
        },
    }


class C2aiTableCreator:
    newTableName: str | None;
    sourceDataId: int;
    engine: _engine.Engine;
    edTablesDict: dict;
    def __init__(self, engine, sourceDataId):
        self.sourceDataId = sourceDataId
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
        """
        Converts unix timestamp in milliseconds to pandas datetime.
        """
        return pd.to_datetime(col, unit="ms", origin="unix", errors="coerce", utc=True)
    
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
        
    def create_postgre_table(self) -> bool:
        already_exists_query = """
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = :table_name
            );
        """
        query = f"""
            CREATE TABLE IF NOT EXISTS "{self.newTableName}" (
                date_time TIMESTAMPTZ PRIMARY KEY,

                battery_voltage NUMERIC(10,3),
                supply_voltage NUMERIC(10,3),

                wind_speed NUMERIC(10,3),
                wind_direction NUMERIC(10,3),

                air_temperature NUMERIC(10,3),
                relative_humidity NUMERIC(10,3),
                dew_point NUMERIC(10,3),

                solar_radiation NUMERIC(10,3),
                atmospheric_pressure NUMERIC(10,3),

                hourly_evapotranspiration NUMERIC(10,3),
                daily_evapotranspiration NUMERIC(10,3),

                rain_intensity NUMERIC(10,3),
                daily_rainfall NUMERIC(10,3),
                total_rainfall NUMERIC(10,3),

                microclimate_temperature NUMERIC(10,3),
                microclimate_relative_humidity NUMERIC(10,3),
                microclimate_dew_point NUMERIC(10,3),
                microclimate_absolute_humidity NUMERIC(10,3),
                microclimate_upper_leaf_wetness NUMERIC(10,3),
                microclimate_lower_leaf_wetness NUMERIC(10,3)
            );
        """
        
        with self.engine.connect() as connection:
            alreadyExists = connection.execute(
                text(already_exists_query),
                {"table_name": self.newTableName}
            ).scalar()
            if alreadyExists:
                return True
            connection.execute(text(query))
            connection.commit()

            self.addStationColumnsToTable()
            return False
    
    def addStationColumnsToTable(self):
        stationIdQuery = text('SELECT "StationId" FROM "Stations" WHERE "HardwareId" = :hwid')
        with self.engine.begin() as conn:
            stationId = conn.execute(stationIdQuery, {"hwid": self.newTableName}).scalar()

        query = text(""" 
            INSERT INTO "StationColumn"
            ("table_name","column_name","data_type","unit","aggregation","param","confidence","source", "station_id")
            VALUES
                -- volt
                (:table_name,'battery_voltage','NUMERIC(10,3)','V',NULL,'battery',NULL,'manufacturer_template', :stationId),
                (:table_name,'supply_voltage','NUMERIC(10,3)','V',NULL,'supply',NULL,'manufacturer_template', :stationId),

                -- wind
                (:table_name,'wind_speed','NUMERIC(10,3)','m/s',ARRAY['avg','min','max']::TEXT[],'wind speed',NULL,'manufacturer_template', :stationId),
                (:table_name,'wind_direction','NUMERIC(10,3)','deg',NULL,'wind direction',NULL,'manufacturer_template', :stationId),

                -- air
                (:table_name,'air_temperature','NUMERIC(10,3)','°C',ARRAY['avg','min','max']::TEXT[],'temperature',NULL,'manufacturer_template', :stationId),
                (:table_name,'relative_humidity','NUMERIC(10,3)','%',ARRAY['avg','min','max']::TEXT[],'relative humidity',NULL,'manufacturer_template', :stationId),
                (:table_name,'dew_point','NUMERIC(10,3)','°C',NULL,'dew point',NULL,'manufacturer_template', :stationId),

                -- radiation / pressure
                (:table_name,'solar_radiation','NUMERIC(10,3)','W/m²',ARRAY['sum']::TEXT[],'solar radiation',NULL,'manufacturer_template', :stationId),
                (:table_name,'atmospheric_pressure','NUMERIC(10,3)','hPa',NULL,'atmospheric pressure',NULL,'manufacturer_template', :stationId),

                -- ET
                (:table_name,'hourly_evapotranspiration','NUMERIC(10,3)','mm/h',NULL,'evapotranspiration',NULL,'manufacturer_template', :stationId),
                (:table_name,'daily_evapotranspiration','NUMERIC(10,3)','mm/d',NULL,'daily evapotranspiration',NULL,'manufacturer_template', :stationId),

                -- rain
                (:table_name,'rain_intensity','NUMERIC(10,3)','mm/h',NULL,'rain intensity',NULL,'manufacturer_template', :stationId),
                (:table_name,'daily_rainfall','NUMERIC(10,3)','mm',ARRAY['sum']::TEXT[],'precipitation',NULL,'manufacturer_template'),
                (:table_name,'total_rainfall','NUMERIC(10,3)','mm',NULL,'total rainfall',NULL,'manufacturer_template', :stationId),

                -- microclimate
                (:table_name,'microclimate_temperature','NUMERIC(10,3)','°C',NULL,'microclimate temperature',NULL,'manufacturer_template', :stationId),
                (:table_name,'microclimate_relative_humidity','NUMERIC(10,3)','%',NULL,'microclimate relative humidity',NULL,'manufacturer_template', :stationId),
                (:table_name,'microclimate_dew_point','NUMERIC(10,3)','°C',NULL,'microclimate dew point',NULL,'manufacturer_template', :stationId),
                (:table_name,'microclimate_absolute_humidity','NUMERIC(10,3)','g/m³',NULL,'microclimate absolute humidity',NULL,'manufacturer_template', :stationId),
                (:table_name,'microclimate_upper_leaf_wetness','NUMERIC(10,3)','%',NULL,'microclimate upper leaf wetness',NULL,'manufacturer_template', :stationId),
                (:table_name,'microclimate_lower_leaf_wetness','NUMERIC(10,3)','%',NULL,'microclimate lower leaf wetness',NULL,'manufacturer_template', :stationId)

            ON CONFLICT ("table_name","column_name")
            DO UPDATE SET
                "data_type"    = EXCLUDED."data_type",
                "unit"         = EXCLUDED."unit",
                "aggregation"  = EXCLUDED."aggregation",
                "param"        = EXCLUDED."param",
                "confidence"   = EXCLUDED."confidence",
                "source"       = EXCLUDED."source",
                "station_id"   = EXCLUDED."station_id",
                "updated_at"   = NOW()
            WHERE
                "StationColumn"."data_type"    IS DISTINCT FROM EXCLUDED."data_type"
                OR "StationColumn"."unit"      IS DISTINCT FROM EXCLUDED."unit"
                OR "StationColumn"."aggregation" IS DISTINCT FROM EXCLUDED."aggregation"
                OR "StationColumn"."param"     IS DISTINCT FROM EXCLUDED."param"
                OR "StationColumn"."confidence" IS DISTINCT FROM EXCLUDED."confidence"
                OR "StationColumn"."source"    IS DISTINCT FROM EXCLUDED."source"
                OR "StationColumn"."station_id" IS DISTINCT FROM EXCLUDED."station_id";
        """)

        with self.engine.begin() as connection:
            connection.execute(
                query,
                {"table_name": self.newTableName, "stationId": stationId}
            )
        
    
    def get_highest_starting_timestamp(self):
        """
        Docstring for get_highest_starting_timestamp
        """
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
            f"WHERE DATE_TIME >= FROM_UNIXTIME({unixStartTime});"
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

    def transformPluviometerColumnsOnFinalDf(self, df):
        colsToChange = list(TableColumnNameTransformer.MEAS_RENAME_BY_TYPE.get(TableType.PluviometerTable.value, {}).values())
        df = df.sort_values("date_time")

        df[colsToChange] = df[colsToChange].fillna(0)

        lastTotalRainfallVal = 0.0
        lastDailyRainfallVal = 0.0
        for idx, row in df[colsToChange].iterrows():
            cellTotalRainFall = float(row["total_rainfall"])
            cellDailyRainFall = float(row["daily_rainfall"])
            cellRainIntensity = float(row["rain_intensity"])

            if cellTotalRainFall != 0:
                lastTotalRainfallVal = cellTotalRainFall
            else:
                df.at[idx, "total_rainfall"] = lastTotalRainfallVal

            if cellDailyRainFall > 0:
                if cellDailyRainFall == lastDailyRainfallVal:  
                    lastDailyRainfallVal = 0.0
                    df.at[idx, "daily_rainfall"] = 0.0
                elif cellDailyRainFall > lastDailyRainfallVal and cellRainIntensity > 0:
                    df.at[idx, "daily_rainfall"] = cellDailyRainFall - lastDailyRainfallVal
                    lastDailyRainfallVal = cellDailyRainFall
                elif cellDailyRainFall > lastDailyRainfallVal and cellRainIntensity == 0.0:
                    df.at[idx, "daily_rainfall"] = 0.0
                else:
                    lastDailyRainfallVal = cellDailyRainFall
        return df

    
    def getFullDataDf(self, startQueryTime : datetime | None = None):
        dfList = []
        unixStartTime = None
        if startQueryTime is not None:
            unixStartTime = int(startQueryTime.timestamp())
        if unixStartTime is None: unixStartTime = self.get_highest_starting_timestamp()
        for table in self.edTablesDict:
            dfList.append(self.get_table_data(table, unixStartTime))
        combinedDf = TransformData.combine_dfs_with_diff_timestamp(dfList, "date_time")
        return self.transformPluviometerColumnsOnFinalDf(combinedDf)
