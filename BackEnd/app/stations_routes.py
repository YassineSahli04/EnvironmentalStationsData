from fastapi import APIRouter
from BackEnd.PostgreSQL.PostgreSQL import PostgreSQL

router = APIRouter(
    prefix="/api/user",
    tags=["stations"],
)

@router.get('/stations-Geojson')
def user_stations_geojson():
    db = PostgreSQL()
    return db.get_stations_Geojson_object()