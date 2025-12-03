from fastapi import APIRouter, Query
from BackEnd.PostgreSQL.PostgreSQL import PostgreSQL
from BackEnd.ClimateFieldStations.CfStation import CfStation
from datetime import datetime

router = APIRouter(
    prefix="/api/stations",
    tags=["stations"],
)

@router.get('')
def get_stations(typeFilter:list[str]= Query(None, alias="type[]")):
    db = PostgreSQL()
    return db.get_all_station_objects(typeFilter)

@router.get('/geojson')
def get_stations_geojson(typeFilter: list[str]|None = Query(None, alias="type[]")):
    db = PostgreSQL()
    return db.get_stations_Geojson_object(typeFilter)

@router.get('/station/{stationId}/{sensorId}')
async def get_station_sensor_data(stationId: str|None, sensorId: str|None, dataGroup: str | None = Query(None), startDtUTC: datetime | None = Query(None), endDtUTC: datetime | None = Query(None)):
    if stationId is None:
        raise AttributeError('Station Id is not defined', stationId)
    if sensorId is None:
        raise AttributeError('Sensor Id is not defined', sensorId)
    
    station = CfStation(stationId)
    return station.getSensorData(
        sensorId=sensorId,
        dataGroup=dataGroup,
        startDtUTC=startDtUTC,
        endDtUTC=endDtUTC,
    )


