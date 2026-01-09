from BackEnd.ClimateFieldStations.API.CfStationAPI import CfStationAPI, CfStationAPIDataGroup
from sqlalchemy import text
import sqlalchemy.engine as _engine
from BackEnd.Utils.TransformData import TransformData
from BackEnd.ClimateFieldStations.Data.CfSensorObject import CfSensorObject
from datetime import datetime, timedelta

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
        requestMetadata = True
        while start <= max:
            end = start + timedelta(days=self.station.QUERY_DAYS_LIMIT_HOURLY)
            if (end > max):
                end = max
            if (start == end):
                break
            try: 
                if requestMetadata:
                    df, self.unitsList = self.station.get_station_data_df(
                        dataGroup,
                        start,
                        end,
                        withColsMetadata=requestMetadata
                    )
                else:
                    df = self.station.get_station_data_df(
                        dataGroup,
                        start,
                        end,
                        withColsMetadata=requestMetadata
                    )
                requestMetadata = False

                if(self.station.Type != 'Aquachek' or self.station.Type != 'Drill and Drop'):
                    df = CfSensorObject.remove_duplicated_columns(df)
                dfDataBatches.append(df)
            except Exception as e:
                print(e)
            start = end 
        if len(dfDataBatches) == 0:
            return None
        if not self.isStationColumnsDefinedInStationColumnTable():
            self.addStationColumnInStationColumnTable()

        return TransformData.combine_df_batches_with_same_columns(dfDataBatches)
    
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
        
    def addStationColumnInStationColumnTable(self):
        if self.unitsList is None:
            raise ValueError(f'No units defined in the Units List for Table {self.newTableName}.')
        
        
        



