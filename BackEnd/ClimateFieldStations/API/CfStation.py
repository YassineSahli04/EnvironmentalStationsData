from BackEnd.ClimateFieldStations.API.ApiCalls import ApiCalls 
from BackEnd.PostgreSQL.StationDbObject import StationDataGroup, StationDbObject
import sqlalchemy.engine as _engine
from BackEnd.ClimateFieldStations.Data.CfSensorObject import CfSensorObject
from datetime import timezone, timedelta


class CfStation(StationDbObject):
    DATA_ACCESS_DAYS_LIMIT = 365
    QUERY_DAYS_LIMIT_HOURLY = 30

    engine = _engine.Engine
    def __init__(
        self,
        engine : _engine.Engine,
        stationId: str
    ):
        super().__init__(stationId)
        self.engine = engine
        info = self.get_station_info_from_api()
        self.Name = info.get("name").get("custom") if self.Name is None else self.Name # type: ignore
        self.Manufacturer = "Pessl" if self.Manufacturer is None else self.Manufacturer # type: ignore
        self.Longitude = info.get("position").get("geo").get("coordinates")[0] if self.Longitude is None else self.Longitude # type: ignore
        self.Latitude = info.get("position").get("geo").get("coordinates")[1] if self.Latitude is None else self.Latitude # type: ignore
        self.Altitude = info.get("position").get("altitude") if self.Altitude is None else self.Altitude # type: ignore
        self.DataTableName = stationId if self.DataTableName is None else self.DataTableName # type: ignore
        self.Type = self.get_station_type_from_api() if self.Type is None else self.Type
        timezoneOffset = info.get("config", {}).get("timezone_offset", 0) # type: ignore 
        self.DataTimeZone = timezone(timedelta(minutes=timezoneOffset))

        
    def get_station_info_from_api(self):
        endpoint = f'/station/{self.Id}'
        method = 'GET'
        jsonObject = ApiCalls.api_call(method, endpoint)
        return jsonObject
    
    def get_station_min_max_timestamps_from_api(self):
        endpoint = f'/data/{self.Id}'
        method = 'GET'
        return ApiCalls.api_call(method, endpoint)

    def get_all_station_sensors_from_api(self):
        endpoint = f'/station/{self.Id}/sensors'
        method = 'GET'
        return ApiCalls.api_call(method, endpoint)

    def get_station_data_in_timestamp_from_api(self, dataGroup : StationDataGroup, startDate: int, endDate:int):
        endpoint = f'/data/{self.Id}/{dataGroup}/from/{startDate}/to/{endDate}'
        method = 'GET'
        return ApiCalls.api_call(method,endpoint)
    
    def get_station_type_from_api(self):
        stationInfo = self.get_station_info_from_api()
        info = stationInfo.get("info") or {} # type: ignore
        meta = stationInfo.get("meta") or {} # type: ignore

        device_name = info.get("device_name")
        soil_temp = meta.get("soilTemp")
        rain_last = meta.get("rain_last")

        if device_name == "iMetos ECO D3":
            return "Pyranometer"

        if device_name == "uMETOS CLIMA" and soil_temp:
            return "Drill and Drop"

        if device_name == "uMETOS CLIMA" and rain_last is not None:
            return "Pluviometer"

        if device_name == "LoRa CLIMA":
            return "Meteorological"

        if device_name == "LoRa SOIL":
            return "Aquachek"

        return None
    

    def getSensorData(self, sensorId, dataGroup, startDtUTC, endDtUTC, isDataInDf = False): 
        startTimestamp = int(startDtUTC.timestamp())
        endTimestamp = int(endDtUTC.timestamp())
        stationData = self.get_station_data_in_timestamp_from_api( dataGroup, startTimestamp, endTimestamp)
        if (stationData.get("message")):  # type: ignore
            raise Exception(f"Error Occured for station [{self.Id}]: "+ stationData.get("message"))   # type: ignore
        sensor = CfSensorObject(stationData, sensorId, isDataInDf=isDataInDf)
        return sensor
    
    def get_station_data_df(self, dataGroup :StationDataGroup, startDtUTC, endDtUTC):
        startTimestamp = int(startDtUTC.astimezone(timezone.utc).timestamp())
        endTimestamp = int(endDtUTC.astimezone(timezone.utc).timestamp())
            
        st_dataJsonObject = self.get_station_data_in_timestamp_from_api(dataGroup.value, startTimestamp, endTimestamp) # type: ignore
        if (st_dataJsonObject.get("message")): # type: ignore
            raise Exception(f"Error Occured for station [{id}]: "+ st_dataJsonObject.get("message")) # type: ignore
        st_df = CfSensorObject.transform_data_to_df_or_csv(st_dataJsonObject, self.DataTimeZone, isColomnHeaderCombined=True)

        return st_df
        






    


            



