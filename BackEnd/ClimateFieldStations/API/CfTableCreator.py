from BackEnd.ClimateFieldStations.API.CfStationAPI import CfStationAPI, CfStationAPIDataGroup
from sqlalchemy import text
import sqlalchemy.engine as _engine
from BackEnd.Utils.TransformData import TransformData
from BackEnd.ClimateFieldStations.Data.CfSensorObject import CfSensorObject, CfDataType
from datetime import datetime, timedelta, timezone
import pandas as pd

class CfTableCreator:
    station : CfStationAPI
    unitsList: list[tuple[str, str]]
    def __init__(self,engine : _engine.Engine, stationId :str) -> None:
        self.station = CfStationAPI(stationId)
        self.newTableName = stationId
        self.engine = engine

    def add_station_to_stations_table(self):
        query = f"INSERT INTO \"Stations\" (\"Id\", \"Name\", \"Manufacturer\", \"Type\", \"Latitude\", \"Longitude\", \"Altitude\", \"DataTableName\") VALUES (:id, :name, :manufacturer, :type, :latitude, :longitude, :altitude, :tablename)"
        with self.engine.connect() as connection: # type: ignore
            connection.execute(
            text(query),
                {
                    "id": self.station.Id,
                    "name": self.station.Name,
                    "manufacturer": self.station.Manufacturer,
                    "type": self.station.Type,
                    "latitude": self.station.Latitude,
                    "longitude": self.station.Longitude,
                    "altitude": self.station.Altitude,
                    "tablename": self.station.DataTableName,
                }
            )
            connection.commit()

    def getFullDataDf(self, startQueryTime: datetime | None = None, dataGroup :CfStationAPIDataGroup = CfStationAPIDataGroup.hourly):
        minMaxTimeStamps = self.station.get_station_min_max_timestamps_from_api()
        max_str = minMaxTimeStamps["max_date"]  # type: ignore
      
        now = datetime.now(self.station.DataTimeZone)
        if startQueryTime is None:
            startQueryTime = now - timedelta(self.station.DATA_ACCESS_DAYS_LIMIT)
        else:
            startQueryTime += timedelta(minutes=1)
        max = datetime.strptime(max_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=self.station.DataTimeZone)

        if startQueryTime >= max:
            return None

        dfDataBatches = []
        start = startQueryTime
        while start <= max:
            end = start + timedelta(days=self.station.QUERY_DAYS_LIMIT_HOURLY)
            if (end > max):
                end = max
            if (start == end):
                break
            try: 

                df = self.station.get_station_data_df(
                    dataGroup,
                    start,
                    end
                )
                if self.station.Type not in ('Aquachek', 'Drill and Drop'):
                    df = CfSensorObject.remove_duplicated_columns(df)
                dfDataBatches.append(df)
            except Exception as e:
                print(e)
            start = end 
        if len(dfDataBatches) == 0:
            return None
        
        finalDf = TransformData.combine_df_batches_with_same_columns(dfDataBatches)
        if not self.isStationColumnsDefinedInStationColumnTable():
            cols = self.getDfSpecificCols(finalDf)
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
            c for c in df.columns.str.split(" - ").str[0]
            if c != "date_time"
        ]

    def isStationColumnsDefinedInStationColumnTable(self):
        if not self.IsDataTableCreated():
            raise Exception(f"Data Table {self.newTableName} is not created yet.")
        query = text(f"""
            SELECT COUNT(*) 
            FROM "StationColumn"
            WHERE "station_id" = '{self.newTableName}'
            """)
        with self.engine.begin() as connection:
            res = connection.execute(query).scalar()
            if res is None:
                return False
            return res > 0
        
        
    def getColDataStats(self, allCols):
        minMaxTimeStamps = self.station.get_station_min_max_timestamps_from_api()
        max_str = minMaxTimeStamps["max_date"]  # type: ignore
      
        now = datetime.now(timezone.utc)
        startQueryTime = (now - timedelta(self.station.DATA_ACCESS_DAYS_LIMIT)).replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        max = datetime.strptime(max_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=self.station.DataTimeZone)

        if startQueryTime >= max:
            return None

        colsData = {}
        
        start = startQueryTime
        while start <= max:
            end = start + timedelta(days=1) - timedelta(minutes=1)
            if (end > max):
                end = max
            if (start == end):
                break

            startTimestamp = int(start.astimezone(timezone.utc).timestamp())
            endTimestamp = int(end.astimezone(timezone.utc).timestamp())     
            st_dataJsonObject = self.station.get_station_data_in_timestamp_from_api(CfStationAPIDataGroup.hourly.value, startTimestamp, endTimestamp) # type: ignore
            if (st_dataJsonObject.get("message")): # type: ignore
                start = end 
                continue
            if st_dataJsonObject.get('data', {}) == {}:
                start = end 
                continue
            
            dataSections = st_dataJsonObject.get('data')
            sensorIds = [section.get("name_original") for section in dataSections if section.get("name_original") is not None]

            for id in sensorIds:
                if id in colsData:
                    continue
                sensorObj = CfSensorObject(st_dataJsonObject, id)
                if sensorObj.type != CfDataType.Sensor:
                    continue
                colsData[id] = sensorObj.getSensorDataInfo()

            if set(colsData.keys()) == set(allCols):
                return colsData
            start = end


    
    
    def addStationColumnInStationColumnTable(self, cols):
        if self.unitsList is None:
            raise ValueError(f'No units defined in the Units List for Table {self.newTableName}.')
        
        if self.station.Type not in ('Aquachek', 'Drill and Drop'):
            return


        
        
        
        



