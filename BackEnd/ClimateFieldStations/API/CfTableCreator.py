from BackEnd.ClimateFieldStations.API.CfStation import CfStation
from sqlalchemy import text
from BackEnd.Utils.TransformData import TransformData
from BackEnd.ClimateFieldStations.Data.CfSensorObject import CfSensorObject
from BackEnd.PostgreSQL.StationDbObject import StationDataGroup
from datetime import datetime, timezone, timedelta

class CfTableCreator(CfStation):
    def __init__(self, stationId :str) -> None:
        super().__init__(stationId)

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

    def getFullStationData(self, dataGroup :StationDataGroup = StationDataGroup.hourly):
        minMaxTimeStamps = self.get_station_min_max_timestamps_from_api()
        max_str = minMaxTimeStamps["max_date"]  # type: ignore

        now = datetime.now(self.DataTimeZone)
        min = now - timedelta(self.DATA_ACCESS_DAYS_LIMIT)
        max = datetime.strptime(max_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=self.DataTimeZone)

        if min >= max:
            return []

        dfDataBatches = []
        start = min
        while start < max:
            end = start + timedelta(days=self.QUERY_DAYS_LIMIT_HOURLY)
            if (end > max):
                end = max
            if (start == end):
                break
            try:
                stationData = self.get_station_data_in_timestamp_from_api(dataGroup.value, int(start.astimezone(timezone.utc).timestamp()), int(end.astimezone(timezone.utc).timestamp()))  # type: ignore
                if (stationData.get("message")):  # type: ignore
                    raise Exception(f"Error Occured for station [{self.Id}]: "+ stationData.get("message"))   # type: ignore
                df = CfSensorObject.transform_data_to_df_or_csv(stationData, self.DataTimeZone, isColomnHeaderCombined=True)
                df = CfSensorObject.remove_duplicated_columns(df)
                dfDataBatches.append(df)
            except Exception as e:
                print(e)
            start = end
  
        return TransformData.combine_df_batches_with_same_columns(dfDataBatches)

    
