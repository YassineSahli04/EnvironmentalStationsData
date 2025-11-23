from BackEnd.ClimateFieldStations.ApiCalls import ApiCalls
from BackEnd.GeoJson.GeoJsonObject import GeoJsonObject
from BackEnd.ClimateFieldStations.CfStation import CfStation
from BackEnd.ClimateFieldStations.TransformData import TransformData
from BackEnd.ClimateFieldStations.CfStation import StationDataGroup

class CfUser:
    def __init__(self):
        pass
    def get_user_info(self):
        endpoint = '/user'
        method = 'GET'
        return ApiCalls.api_call(method, endpoint)

    @staticmethod
    def get_all_stations():
        endpoint='/user/stations'
        method='GET'
        return ApiCalls.api_call(method, endpoint)

    def get_all_user_stations_data(self, dataGroup :StationDataGroup, startDtUTC, endDtUTC, isCsv = False):
        startTimestamp = int(startDtUTC.timestamp())
        endTimestamp = int(endDtUTC.timestamp())
        stations = self.get_all_stations()
        dfs = []
        for st in stations:
            id = st["name"]["original"] # type: ignore
            station = CfStation(id)
            
            st_dataJsonObject = station.get_station_data_in_timestamp_from_api(dataGroup, startTimestamp, endTimestamp)
            st_df = TransformData.transform_data_to_df_or_csv(st_dataJsonObject)
            dfs.append(st_df)
        final_df = TransformData.combine_dfs_with_same_timestamp(dfs)
        if isCsv: final_df.to_csv("test.csv", index=False); return

        return final_df
