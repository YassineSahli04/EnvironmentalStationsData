from fastapi import APIRouter, Query
from BackEnd.PostgreSQL.PostgreSQL import PostgreSQL

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


