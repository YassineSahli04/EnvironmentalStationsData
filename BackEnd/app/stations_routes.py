from fastapi import APIRouter
from BackEnd.ClimateFieldStations.user import get_all_user_stations_info_geojson

router = APIRouter(
    prefix="/api/user",
    tags=["stations"],
)

@router.get('/stations-Geojson')
def user_stations_geojson():
    return get_all_user_stations_info_geojson()