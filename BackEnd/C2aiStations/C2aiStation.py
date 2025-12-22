from BackEnd.PostgreSQL.PostgreSQL import PostgreSQL
from BackEnd.PostgreSQL.StationDbObject import StationDataGroup, StationDbObject
from BackEnd.C2aiStations.C2aiSensor import C2aiSensor, granularityMap
import sqlalchemy.engine as _engine

class C2aiStation(StationDbObject):
    engine = _engine.Engine
    def __init__(self, stationId: str):
        super().__init__(stationId)
        self.engine = PostgreSQL().engine
        self.set_or_update_station_metadata(self.engine)
        self.set_last_data_point_time(self.engine)

    def getSensorData(self, sensorId, dataGroup, startDtUTC, endDtUTC):
        dataGroup = StationDataGroup(dataGroup)
        if dataGroup not in granularityMap:
            raise ValueError(f"Invalid dataGroup: {dataGroup}")
        step = granularityMap[dataGroup]

        queryParams = {
            "step": step,
            "start_dt": startDtUTC,
            "end_dt": endDtUTC, 
        }
        sensor = C2aiSensor(self.Id, sensorId, isDataInDf=False)
        sensor.setSensorData(self.engine, queryParams)
        return sensor


