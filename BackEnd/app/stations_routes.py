from fastapi import APIRouter, Query, HTTPException
from BackEnd.PostgreSQL.PostgreSQL import PostgreSQL
from BackEnd.PostgreSQL.StationDbObject import StationDbObject
from datetime import datetime
import  logging
from BackEnd.Utils.DateTimeHelper import DateTimeHelper

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/stations",
    tags=["stations"],
)
db = PostgreSQL()

@router.get('/all')
def get_stations(typeFilter:list[str]= Query(None, alias="type[]")):
    stations = db.get_all_station_objects(typeFilter)
    stsSerializable = []
    for st in stations:
        stsSerializable.append(st.getSerializableObj())
    return stsSerializable

@router.get('/geojson')
def get_stations_geojson(typeFilter: list[str]|None = Query(None, alias="type[]")):
    return db.get_stations_Geojson_object(typeFilter)

@router.get('/station/{stationId}/{sensorId}')
def get_station_sensor_data(stationId: str, sensorId: str, dataGroup: str | None = Query(None), startDtUTC: datetime | None = Query(None), endDtUTC: datetime | None = Query(None)): 
    station = StationDbObject(db.engine, stationId)

    startDtUTC = DateTimeHelper.to_utc(startDtUTC)
    endDtUTC = DateTimeHelper.to_utc(endDtUTC)

    try:    
        return station.getSensorAllDataColumns(sensorId=sensorId, dataGroup=dataGroup, startDtUTC=startDtUTC, endDtUTC=endDtUTC) # type: ignore
    except ValueError as e:
        logger.warning(
            "%s FROM:%s - To:%s ", e, startDtUTC, endDtUTC
        )
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(
            "Error while getting sensor data: station=%s sensor=%s (%s)",
            stationId, sensorId, e
        )
        raise HTTPException(status_code=500, detail="Internal Server Error")


### SCHEDULER CODE FOR UPDATING THE DB FROM THE SERVER 
@router.post("/server/update-db")
def update_db():
    db = PostgreSQL()
    db.create_update_all_stations_data_tables()