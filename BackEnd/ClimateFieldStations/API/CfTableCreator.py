from BackEnd.ClimateFieldStations.API.CfStationAPI import CfStationAPI, CfStationAPIDataGroup
from sqlalchemy import text
import sqlalchemy.engine as _engine
from BackEnd.Utils.TransformData import TransformData
from BackEnd.ClimateFieldStations.Data.CfSensorObject import CfSensorObject
from datetime import datetime, timedelta

class CfTableCreator:
    station : CfStationAPI
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
                df = self.station.get_station_data_df(dataGroup, start, end)
                if(self.station.Type != 'Aquachek' or self.station.Type != 'Drill and Drop'):
                    df = CfSensorObject.remove_duplicated_columns(df)
                dfDataBatches.append(df)
            except Exception as e:
                print(e)
            start = end 
        if len(dfDataBatches) == 0:
            return None
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

    
