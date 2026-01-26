from fastapi import APIRouter, Query, HTTPException
from BackEnd.PostgreSQL.PostgreSQL import PostgreSQL
from BackEnd.PostgreSQL.StationDbObject import StationDbObject
from datetime import datetime
import  logging, traceback
from BackEnd.Utils.DateTimeHelper import DateTimeHelper

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/stations",
    tags=["stations"],
)
db = PostgreSQL()

@router.get('/all')
def get_stations(typeFilter:list[str]= Query(None, alias="type[]")):
    try:
        stations = db.get_all_station_objects(typeFilter)
        stsSerializable = []
        for st in stations:
            stsSerializable.append(st.getSerializableObj())
        return stsSerializable
    except ValueError as e:
        logger.warning(
            "%s", e
        )
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        tb_last = traceback.extract_tb(e.__traceback__)[-1]
        logger.error(
            "Error while getting all stations: (%s) at %s:%s in %s",
            e,
            tb_last.filename,
            tb_last.lineno,
            tb_last.name,
        )
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.get('/geojson')
def get_stations_geojson(typeFilter: list[str]|None = Query(None, alias="type[]")):
    try:
        return db.get_stations_Geojson_object(typeFilter)
    except ValueError as e:
        logger.warning(
            "%s", e
        )
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        tb_last = traceback.extract_tb(e.__traceback__)[-1]
        logger.error(
            "Error while getting GeoJson file: (%s) at %s:%s in %s",
            e,
            tb_last.filename,
            tb_last.lineno,
            tb_last.name,
        )
        raise HTTPException(status_code=500, detail="Internal Server Error")

    
@router.get('/station/{stationId}/sensors')
def get_station_sensons_data(stationId: str, sensorsId: list[str] | None = Query(None, alias="sensorsId[]"), dataGroup: str | None = Query(None), startDtUTC: datetime | None = Query(None), endDtUTC: datetime | None = Query(None)):     
    try: 
        station = StationDbObject(db.engine, stationId)

        startDtUTC = DateTimeHelper.to_utc(startDtUTC)
        endDtUTC = DateTimeHelper.to_utc(endDtUTC)

        if sensorsId is None or len(sensorsId) == 0: 
            raise Exception("Sensors are not defined.")  
        if len(sensorsId) == 1:
            sensorId = sensorsId[0]
            return station.getSensorAllDataColumns(sensorId=sensorId, dataGroup=dataGroup, startDtUTC=startDtUTC, endDtUTC=endDtUTC) # type: ignore
        if len(sensorsId) > 1:
            return station.getSensonsDefaultDataColumns(sensorIdsList=sensorsId, dataGroup=dataGroup, startDtUTC=startDtUTC, endDtUTC=endDtUTC) # type: ignore
    
    except ValueError as e:
        logger.warning(
            "%s FROM:%s - To:%s ", e, startDtUTC, endDtUTC
        )
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        tb_last = traceback.extract_tb(e.__traceback__)[-1]
        logger.error(
            "Error while getting sensor data: station=%s sensor=%s (%s) at %s:%s in %s",
            stationId,
            sensorId,
            e,
            tb_last.filename,
            tb_last.lineno,
            tb_last.name,
        )
        raise HTTPException(status_code=500, detail="Internal Server Error")


### SCHEDULER CODE FOR UPDATING THE DB FROM THE SERVER 
@router.post("/server/update-db")
def update_db():
    db = PostgreSQL()
    db.create_update_all_stations_data_tables()