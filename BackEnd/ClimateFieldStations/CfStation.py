from BackEnd.ClimateFieldStations.ApiCalls import ApiCalls 
from BackEnd.PostgreSQL.PostgreSQL import PostgreSQL
from BackEnd.PostgreSQL.StationDbObject import StationDbObject
import sqlalchemy.engine as _engine
from sqlalchemy import text
from BackEnd.ClimateFieldStations.Data.CfSensorObject import CfSensorObject

from enum import Enum
class StationDataGroup(Enum):
    raw = "raw"
    hourly ="hourly"
    daily = "daily"
    monthly = "monthly"

class CfStation(StationDbObject):
    engine = _engine.Engine
    def __init__(
        self,
        stationId: str,
        name: str | None = None,
        location: str | None = None,
        manufacturer: str | None = None,
        type: str | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
        altitude: float | None = None,
        data_source_id: int | None = None,
        data_table_name: str | None = None,
    ):
        super().__init__(stationId, name, location, manufacturer, type, latitude, longitude, altitude, data_source_id, data_table_name)
        self.engine = PostgreSQL().engine
        info = self.get_station_info_from_api()
        self.Name = info.get("name").get("custom") if self.Name is None else self.Name # type: ignore
        self.Manufacturer = "Pessl" if self.Manufacturer is None else self.Manufacturer # type: ignore
        self.Longitude = info.get("position").get("geo").get("coordinates")[0] if self.Longitude is None else self.Longitude # type: ignore
        self.Latitude = info.get("position").get("geo").get("coordinates")[1] if self.Latitude is None else self.Latitude # type: ignore
        self.Altitude = info.get("position").get("altitude") if self.Altitude is None else self.Altitude # type: ignore
        self.DataTableName = stationId if self.DataTableName is None else self.DataTableName # type: ignore
        self.Type = self.get_station_type_from_api() if self.Type is None else self.Type

        
    def get_station_info_from_api(self):
        endpoint = f'/station/{self.Id}'
        method = 'GET'
        jsonObject = ApiCalls.api_call(method, endpoint)
        return jsonObject

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

    def getSensorData(self, sensorId, dataGroup, startDtUTC, endDtUTC, isDataInDf = False): 
        startTimestamp = int(startDtUTC.timestamp())
        endTimestamp = int(endDtUTC.timestamp())
        stationData = self.get_station_data_in_timestamp_from_api( dataGroup, startTimestamp, endTimestamp)
        sensor = CfSensorObject(stationData, sensorId, isDataInDf=isDataInDf)

        return sensor
            



