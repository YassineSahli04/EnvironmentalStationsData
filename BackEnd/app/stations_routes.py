from fastapi import APIRouter, Query, HTTPException
from BackEnd.PostgreSQL.PostgreSQL import PostgreSQL
from BackEnd.PostgreSQL.StationDbObject import StationDbObject
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

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
async def get_station_sensor_data(stationId: str, sensorId: str, dataGroup: str | None = Query(None), startDtUTC: datetime | None = Query(None), endDtUTC: datetime | None = Query(None)): 
    db = PostgreSQL()
    station = StationDbObject(db.engine, stationId)
    station.set_station_metadata()
    
    try:    
        return station.getSensorData(sensorId=sensorId, dataGroup=dataGroup, startDtUTC=startDtUTC, endDtUTC=endDtUTC) # type: ignore
    except Exception as e:
        logger.exception(
            "Error while getting sensor data for station=%s sensor=%s", stationId, sensorId
        )
        logger.exception(
            e
        )
        raise HTTPException(
            status_code=500,
            detail=e
        ) from e
        




### SCHEDULER CODE FOR UPDATING THE DB FROM THE SERVER 
@router.post("/server/update-db")
def update_db():
    db = PostgreSQL()
    db.create_update_all_stations_data_tables()