from BackEnd.PostgreSQL.StationDbObject import StationSerializable, StationDbObject
from langchain.tools import tool
from BackEnd.app.db import db
from dataclasses import asdict

@tool("get_available_stations", description="Get a list of stations with their metadata.")
def get_available_stations() -> list[dict]:
    if db is None:
        raise Exception("The db instance has not been initialized")
    stations = db.get_all_station_objects()
    stationsData = []
    for st in stations:
        data = {"StationId": st.Id, "StationName": st.Name, "StationLocation": st.Location, "StationManufacturer": st.Manufacturer, "StationType": st.Type, "StationState": st.State}
        stationsData.append(data)   
    return stationsData

@tool("set_station", description="Select a station by id and return its metadata.")
def set_station(station_id: str) -> dict:
    if db is None:
        raise Exception("The db instance has not been initialized")
    st = StationDbObject(db.engine, int(station_id))
    if not hasattr(st, "State"):
        raise ValueError("Station not found")
    serial = st.getSerializableObj()
    return asdict(serial)
