from .API_call import api_call
from .GeoJson.GeoJsonObject import GeoJsonObject
from .station import get_station_data_in_timestamp, get_station_info
from .transform_data import transform_data_to_df_or_csv, combine_dfs_with_same_timestamp

def get_user_info():
    endpoint = '/user'
    method = 'GET'
    return api_call(method, endpoint)

def get_all_stations():
    endpoint='/user/stations'
    method='GET'
    return api_call(method, endpoint)

def get_all_user_stations_data(dataGroup, startDtUTC, endDtUTC, isCsv = False):
    startTimestamp = int(startDtUTC.timestamp())
    endTimestamp = int(endDtUTC.timestamp())
    stations = get_all_stations()
    dfs = []
    for st in stations:
        id = st["name"]["original"]
        st_dataJsonObject = get_station_data_in_timestamp(id, dataGroup, startTimestamp, endTimestamp)
        st_df = transform_data_to_df_or_csv(st_dataJsonObject)
        dfs.append(st_df)
    final_df = combine_dfs_with_same_timestamp(dfs)
    if isCsv: final_df.to_csv("test.csv", index=False); return

    return final_df

def get_all_user_stations_info_geojson():
    stations = get_all_stations()
    geoJson = GeoJsonObject()
    for st in stations:
        feature = get_station_info(st["name"]["original"], isGeoJsonFeature=True)
        geoJson.add_feature(feature)
    return geoJson.to_dict()