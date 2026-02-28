from langchain.tools import tool
from urllib import error, request
import json
import os


def _backend_base_url() -> str:
    return os.getenv("BACKEND_URL", "http://backend:8000").rstrip("/")


def _get_json(path: str):
    url = f"{_backend_base_url()}{path}"
    req = request.Request(url, method="GET")

    try:
        with request.urlopen(req, timeout=10) as response:
            return json.load(response)
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        if exc.code == 404:
            raise ValueError("Station not found") from exc
        raise RuntimeError(f"Backend request failed ({exc.code}): {detail}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"Unable to reach backend at {url}") from exc

@tool("get_available_stations", description="Get a list of stations with their metadata.")
def get_available_stations() -> list[dict]:
    stations = _get_json("/api/agent/stations")
    stationsData = []
    for st in stations:
        data = {
            "StationId": st["Id"],
            "StationName": st["Name"],
            "StationLocation": st["Location"],
            "StationManufacturer": st["Manufacturer"],
            "StationType": st["Type"],
            "StationState": st["State"],
        }
        stationsData.append(data)   
    return stationsData

@tool("set_station", description="Select a station by id and return its metadata.")
def set_station(station_id: str) -> dict:
    return _get_json(f"/api/agent/stations/{int(station_id)}")
