from BackEnd.ClimateFieldStations.ApiCalls import ApiCalls
from BackEnd.ClimateFieldStations.CfStation import CfStation
from BackEnd.ClimateFieldStations.TransformData import TransformData
from BackEnd.ClimateFieldStations.CfStation import StationDataGroup

class CfUser:
    def __init__(self):
        pass
    def get_user_info_from_api(self):
        endpoint = '/user'
        method = 'GET'
        return ApiCalls.api_call(method, endpoint)

    @staticmethod
    def get_all_stations_from_api():
        endpoint='/user/stations'
        method='GET'
        return ApiCalls.api_call(method, endpoint)

    def get_all_user_stations_data_from_api(self, dataGroup :StationDataGroup, startDtUTC, endDtUTC, isCsv = False):
        stations = self.get_all_stations_from_api()
        dfs = []
        for st in stations:
            id = st["name"]["original"] # type: ignore
            st_df = self.get_station_data_df(id, dataGroup, startDtUTC, endDtUTC)
            dfs.append(st_df)
        final_df = TransformData.combine_dfs_with_same_timestamp(dfs)
        if isCsv: final_df.to_csv("test.csv", index=False); return

        return final_df
    
    def get_station_data_df(self, stationId,  dataGroup :StationDataGroup, startDtUTC, endDtUTC):
        startTimestamp = int(startDtUTC.timestamp())
        endTimestamp = int(endDtUTC.timestamp())
        station = CfStation(stationId)
            
        st_dataJsonObject = station.get_station_data_in_timestamp_from_api(dataGroup, startTimestamp, endTimestamp)
        if (st_dataJsonObject.get("message")):
            raise Exception(f"Error Occured for station [{id}]: "+ st_dataJsonObject.get("message"))
        st_df = TransformData.transform_data_to_df_or_csv(st_dataJsonObject)

        return st_df
        

