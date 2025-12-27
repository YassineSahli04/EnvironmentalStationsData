from BackEnd.ClimateFieldStations.API.CfStation import CfStation
from sqlalchemy import text
import sqlalchemy.engine as _engine
from BackEnd.Utils.TransformData import TransformData
from BackEnd.ClimateFieldStations.Data.CfSensorObject import CfSensorObject
from BackEnd.PostgreSQL.StationDbObject import StationDataGroup
from datetime import datetime, timedelta

class CfTableCreator(CfStation):

    def __init__(self,engine : _engine.Engine, stationId :str) -> None:
        super().__init__(engine, stationId)
        self.newTableName = stationId

    def add_station_to_db(self):
        query = f"INSERT INTO \"Stations\" (\"Id\", \"Name\", \"Manufacturer\", \"Type\", \"Latitude\", \"Longitude\", \"Altitude\", \"DataTableName\") VALUES (:id, :name, :manufacturer, :type, :latitude, :longitude, :altitude, :tablename)"
        with self.engine.connect() as connection: # type: ignore
            connection.execute(
            text(query),
                {
                    "id": self.Id,
                    "name": self.Name,
                    "manufacturer": self.Manufacturer,
                    "type": self.Type,
                    "latitude": self.Latitude,
                    "longitude": self.Longitude,
                    "altitude": self.Altitude,
                    "tablename": self.DataTableName,
                }
            )
            connection.commit()

    def getFullDataDf(self, startQueryTime: datetime | None = None, dataGroup :StationDataGroup = StationDataGroup.hourly):
        minMaxTimeStamps = self.get_station_min_max_timestamps_from_api()
        max_str = minMaxTimeStamps["max_date"]  # type: ignore

        now = datetime.now(self.DataTimeZone)
        if startQueryTime is None:
            startQueryTime = now - timedelta(self.DATA_ACCESS_DAYS_LIMIT)
        max = datetime.strptime(max_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=self.DataTimeZone)

        if startQueryTime >= max:
            return []

        dfDataBatches = []
        start = startQueryTime
        while start < max:
            end = start + timedelta(days=self.QUERY_DAYS_LIMIT_HOURLY)
            if (end > max):
                end = max
            if (start == end):
                break
            try: 
                df = self.get_station_data_df(dataGroup, start, end)
                df = CfSensorObject.remove_duplicated_columns(df)
                dfDataBatches.append(df)
            except Exception as e:
                print(e)
            start = end
  
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

    
