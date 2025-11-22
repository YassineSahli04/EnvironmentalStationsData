from BackEnd.API_call import api_call 
from BackEnd.GeoJson.GeoJsonStationInfoFeature import GeoJsonStationInfoFeature

def get_station_info(stationId, isGeoJsonFeature=False):
    endpoint = f'/station/{stationId}'
    method = 'GET'
    jsonObject = api_call(method, endpoint)
    if isGeoJsonFeature:
        return GeoJsonStationInfoFeature(jsonObject)    
    return jsonObject

def get_all_station_sensors(stationId):
    endpoint = f'/station/{stationId}/sensors'
    method = 'GET'
    return api_call(method, endpoint)

def get_station_data_in_timestamp(stationId, dataGroup, startDate, endDate):
    endpoint = f'/data/{stationId}/{dataGroup}/from/{startDate}/to/{endDate}'
    method = 'GET'
    return api_call(method,endpoint)
