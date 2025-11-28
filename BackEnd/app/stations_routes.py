from fastapi import APIRouter, Query
from BackEnd.PostgreSQL.PostgreSQL import PostgreSQL

router = APIRouter(
    prefix="/api/stations",
    tags=["stations"],
)

@router.get('/a')
def get_stations():
    db = PostgreSQL()
    return db.get_all_station_objects()

@router.get('/geojson')
def get_stations_geojson(typeFilter: list[str]|None = Query(None, alias="type[]")):
    db = PostgreSQL()
    print(typeFilter)
    x =db.get_stations_Geojson_object(typeFilter)
    print(x)
    return x


