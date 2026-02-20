from BackEnd.ClimateFieldStations.API.CfHardwareStationAPI import CfHardwareStationAPI, CfStationAPIDataGroup
from sqlalchemy import text
import sqlalchemy.engine as _engine
from BackEnd.Utils.TransformData import TransformData
from BackEnd.PostgreSQL.StationDbObject import StationDbObject
from BackEnd.ClimateFieldStations.Data.CfSensorObject import CfSensorDataInfo, CfSensorObject, CfDataType
from datetime import datetime, timedelta, timezone
import pandas as pd
from BackEnd.PostgreSQL.StationColumnConverter import StationColumnConverter
from BackEnd.ClimateFieldStations.API.CfAggregationCorrector import CfAggregationCorrector
import os
from redis import Redis
from rq import Queue

class CfTableCreator:
    hardwareStation : CfHardwareStationAPI
    newTableName: str
    def __init__(self,engine : _engine.Engine, hardwareId :str) -> None:
        self.hardwareStation = CfHardwareStationAPI(hardwareId)
        self.newTableName = hardwareId
        self.engine = engine

        redisUrl = os.environ.get("REDIS_URL")
        if redisUrl is None:
            raise ValueError("Redis Url is not defined")
        redisConn = Redis.from_url(redisUrl)
        self.workerQueue = Queue(name="SemanticSearchQueue", connection=redisConn)

    def add_station_to_stations_table(self):
        query = f"INSERT INTO \"Stations\" (\"HardwareId\", \"Name\", \"Manufacturer\", \"Type\", \"Latitude\", \"Longitude\", \"Altitude\", \"DataTableName\") VALUES (:id, :name, :manufacturer, :type, :latitude, :longitude, :altitude, :tablename)"
        with self.engine.connect() as connection: # type: ignore
            connection.execute(
            text(query),
                {
                    "id": self.hardwareStation.Id,
                    "name": self.hardwareStation.Name,
                    "manufacturer": self.hardwareStation.Manufacturer,
                    "type": self.hardwareStation.Type,
                    "latitude": self.hardwareStation.Latitude,
                    "longitude": self.hardwareStation.Longitude,
                    "altitude": self.hardwareStation.Altitude,
                    "tablename": self.hardwareStation.DataTableName,
                }
            )
            connection.commit()

    def getFullDataDf(self, isUpdate: bool = False, dataGroup :CfStationAPIDataGroup = CfStationAPIDataGroup.hourly):
        minMaxTimeStamps = self.hardwareStation.get_station_min_max_timestamps_from_api()
        max_str = minMaxTimeStamps["max_date"]  # type: ignore
      
        now = datetime.now(self.hardwareStation.DataTimeZone)
        if isUpdate:
            isNewTable = False
            startQueryTime = StationDbObject.getStationHardwareLastDataPoint(self.engine, self.newTableName) + timedelta(minutes=1) # type: ignore          
        else:
            isNewTable = True
            startQueryTime = now - timedelta(self.hardwareStation.DATA_ACCESS_DAYS_LIMIT)
            
        max = datetime.strptime(max_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=self.hardwareStation.DataTimeZone)

        if startQueryTime >= max:
            if not self.isStationColumnsDefinedInStationColumnTable():
                cols = StationColumnConverter.getStationTableAvailableColumns(self.engine, self.hardwareStation.Id)
                cols.remove('date_time')
                self.addStationColumnInStationColumnTable(cols)
            return None

        dfDataBatches = []
        start = startQueryTime
        while start <= max:
            end = start + timedelta(days=self.hardwareStation.QUERY_DAYS_LIMIT_HOURLY)
            if (end > max):
                end = max
            if (start == end):
                break
            try: 

                df = self.hardwareStation.get_station_data_df(
                    dataGroup,
                    start,
                    end
                )
                if self.hardwareStation.Type not in ('Aquachek', 'Drill and Drop'):
                    df = CfSensorObject.remove_duplicated_columns(df)
                dfDataBatches.append(df)
            except Exception as e:
                print(e)
            start = end 
        if len(dfDataBatches) == 0:
            return None
        
        finalDf = TransformData.combine_df_batches_with_same_columns(dfDataBatches)
        if isNewTable:
            cols = self.getDfSpecificCols(finalDf)
            self.addStationColumnInStationColumnTable(cols)
        elif not self.isStationColumnsDefinedInStationColumnTable():
            cols = StationColumnConverter.getStationTableAvailableColumns(self.engine, self.hardwareStation.Id)
            cols.remove('date_time')
            self.addStationColumnInStationColumnTable(cols)

        return finalDf
    
    def IsDataTableCreated(self) -> bool:
        already_exists_query = """
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = :table_name
            );
        """
        with self.engine.connect() as connection: # type: ignore
            alreadyExists = connection.execute(
                text(already_exists_query),
                {"table_name": self.newTableName}
            ).scalar()
            if alreadyExists:
                return True
            return False
        
    def getDfSpecificCols(self, df: pd.DataFrame):
        return [
            c for c in df.columns
            if c != "date_time"
        ]

    def getSpecificCols(self, columns: list[str]) -> set[str]:
        return {
            c.split(" - ")[0]
            for c in columns
            if c.split(" - ")[0] != "date_time"
        }

    def isStationColumnsDefinedInStationColumnTable(self):
        if not self.IsDataTableCreated():
            raise Exception(f"Data Table {self.newTableName} is not created yet.")
        query = text(f"""
            SELECT COUNT(*) 
            FROM "StationColumn"
            WHERE "table_name" = '{self.newTableName}'
            """)
        with self.engine.begin() as connection:
            res = connection.execute(query).scalar()
            if res is None:
                return False
            return res > 0
            
    def getColDataStats(self, allCols) -> dict[str, CfSensorDataInfo]:
        allSpecificCols = self.getSpecificCols(allCols)
        minMaxTimeStamps = self.hardwareStation.get_station_min_max_timestamps_from_api()
        max_str = minMaxTimeStamps["max_date"]  # type: ignore
      
        now = datetime.now(timezone.utc)
        startQueryTime = (now - timedelta(self.hardwareStation.DATA_ACCESS_DAYS_LIMIT)).replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        max = datetime.strptime(max_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=self.hardwareStation.DataTimeZone)

        if startQueryTime >= max:
            return {}

        colsData = {}
        
        start = startQueryTime
        while start < max:
            end = min(start + timedelta(days=1), max)
            if start >= end:
                break

            startTimestamp = int(start.astimezone(timezone.utc).timestamp())
            endTimestamp = int(end.astimezone(timezone.utc).timestamp())     
            st_dataJsonObject = self.hardwareStation.get_station_data_in_timestamp_from_api(CfStationAPIDataGroup.hourly.value, startTimestamp, endTimestamp) # type: ignore
            if (st_dataJsonObject.get("message")): # type: ignore
                start += timedelta(days=1)
                continue
            if st_dataJsonObject.get('data', {}) == {}:# type: ignore
                start += timedelta(days=1)
                continue
            
            dataSections = st_dataJsonObject.get('data') # type: ignore
            sensorIds = [section.get("name") for section in dataSections if section.get("name") is not None]

            for id in sensorIds:
                if id in colsData:
                    continue
                sensorObj = CfSensorObject(st_dataJsonObject, id)
                if sensorObj.type != CfDataType.Sensor:
                    continue
                colsData[id] = sensorObj.getSensorDataInfo()

            if set(colsData.keys()) == set(allSpecificCols):
                break
            start += timedelta(days=1)
        return colsData
    
    def addStationColumnInStationColumnTable(self, cols):
        stationIdQuery = text('SELECT "StationId" FROM "Stations" WHERE "HardwareId" = :hwid')
        with self.engine.begin() as conn:
            stationId = conn.execute(stationIdQuery, {"hwid": self.newTableName}).scalar()

        if self.hardwareStation.Type not in ('Aquachek', 'Drill and Drop'):

            colsData = self.getColDataStats(cols)
            query = text("""
                INSERT INTO "StationColumn"
                ("table_name","column_name","data_type","unit","aggregation","param","confidence","source", "station_id")
                VALUES
                (:table_name, :column_name, 'NUMERIC(10,3)', :unit, :aggregation, 'In Process', NULL, 'inferred', :stationId)

                ON CONFLICT ("table_name","column_name")
                DO UPDATE SET
                    "data_type"    = EXCLUDED."data_type",
                    "unit"         = EXCLUDED."unit",
                    "aggregation"  = EXCLUDED."aggregation",
                    "param"        = EXCLUDED."param",
                    "confidence"   = EXCLUDED."confidence",
                    "source"       = EXCLUDED."source",
                    "station_id"       = EXCLUDED."station_id",
                    "updated_at"   = NOW()
                WHERE
                    "StationColumn"."data_type"   IS DISTINCT FROM EXCLUDED."data_type"
                    OR "StationColumn"."unit"     IS DISTINCT FROM EXCLUDED."unit"
                    OR "StationColumn"."aggregation" IS DISTINCT FROM EXCLUDED."aggregation"
                    OR "StationColumn"."param"    IS DISTINCT FROM EXCLUDED."param"
                    OR "StationColumn"."confidence" IS DISTINCT FROM EXCLUDED."confidence"
                    OR "StationColumn"."station_id" IS DISTINCT FROM EXCLUDED."station_id"
                    OR "StationColumn"."source"   IS DISTINCT FROM EXCLUDED."source";
            """)
            with self.engine.begin() as connection:
                for col in cols:
                    specificCol = col.split(" - ")[0]
                    agg = col.split(" - ")[1]
                    sensorData = colsData[specificCol]
                    self.enqueueSemanticSearchJob(col, sensorData)
                    aggCorrected = CfAggregationCorrector.correctAggregation(specificCol, agg)
                    connection.execute(
                        query,
                        {"table_name": self.newTableName, "column_name":col, "unit": sensorData.unit, "aggregation": [aggCorrected], "stationId": stationId}
                    )
        else:
            colsData = self.getColDataStats(cols)
            query = text("""
                INSERT INTO "StationColumn"
                ("table_name","column_name","data_type","unit","aggregation","param","confidence","source", "station_id")
                VALUES
                (:table_name,:column_name,'NUMERIC(10,3)',:unit, :aggregation,:param,NULL,'manufacturer_template', :stationId)
         
                ON CONFLICT ("table_name","column_name")
                DO UPDATE SET
                    "data_type"    = EXCLUDED."data_type",
                    "unit"         = EXCLUDED."unit",
                    "aggregation"  = EXCLUDED."aggregation",
                    "param"        = EXCLUDED."param",
                    "confidence"   = EXCLUDED."confidence",
                    "source"       = EXCLUDED."source",
                    "station_id"       = EXCLUDED."station_id",
                    "updated_at"   = NOW()
                WHERE
                    "StationColumn"."data_type"   IS DISTINCT FROM EXCLUDED."data_type"
                    OR "StationColumn"."unit"     IS DISTINCT FROM EXCLUDED."unit"
                    OR "StationColumn"."aggregation" IS DISTINCT FROM EXCLUDED."aggregation"
                    OR "StationColumn"."param"    IS DISTINCT FROM EXCLUDED."param"
                    OR "StationColumn"."confidence" IS DISTINCT FROM EXCLUDED."confidence"
                    OR "StationColumn"."station_id" IS DISTINCT FROM EXCLUDED."station_id"
                    OR "StationColumn"."source"   IS DISTINCT FROM EXCLUDED."source";
            """)
            with self.engine.begin() as connection:
                for id in colsData:
                    sensorData = colsData[id]
                    connection.execute(
                        query,
                        {"table_name": self.newTableName, "column_name":id, "unit": sensorData.unit, "aggregation": sensorData.aggregationsType, "param":id.lower(), "stationId": stationId}
                    )
    def enqueueSemanticSearchJob(self, columnName, sensorData: CfSensorDataInfo):
        payload = {
            "sensor": sensorData.sensor,
            "unit": sensorData.unit,
            "aggregationsType": sensorData.aggregationsType,
            "dataRange": sensorData.dataRange,
        }

        self.workerQueue.enqueue(
            "Worker.jobs.setColumParam",
            self.hardwareStation.Id,
            columnName,
            payload,
            job_timeout=600,
        )

