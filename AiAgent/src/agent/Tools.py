from typing import Optional
import os
import requests
from datetime import datetime, timedelta

from langchain.tools import tool

def _backend_base_url() -> str:
    return os.getenv("BACKEND_URL", "http://127.0.0.1:8001").rstrip("/")

def _get_json(path: str, params: list[tuple[str, str]] | None = None,  timeout: int = 10):
    base = _backend_base_url().rstrip("/")
    url = f"{base}/{path.lstrip('/')}"

    try:
        resp = requests.get(url, params=params or None, timeout=timeout)
        if resp.status_code == 404:
            raise ValueError("Request not found.")

        resp.raise_for_status()
        return resp.json()

    except requests.exceptions.HTTPError as exc:
        detail = exc.response.text if exc.response is not None else ""
        raise RuntimeError(f"Backend request failed ({resp.status_code}): {detail}") from exc

    except requests.exceptions.RequestException as exc:
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

def get_station_data(
    station_id: str,
    sensors: list[str],
    data_group: str,
    start_dt_utc: str,
    end_dt_utc: str,
) -> list[dict] | None:
    path = f"/api/stations/station/{station_id}/sensors"

    params = [("sensorsId[]", s) for s in sensors]
    params += [("dataGroup", data_group), ("startDtUTC", start_dt_utc), ("endDtUTC", end_dt_utc)]

    data = _get_json(path=path, params=params)
    return data

@tool("prepare_data_request", 
        description=(
        "Extract a partial data request from the user's message. "
        "Copy only fields explicitly provided by the user. "
        "Do not infer or guess missing values. "
        "If the user uses a relative time phrase like 'today' or 'last week', "
        "put it in time_phrase and leave start/end empty unless the user gave exact dates. "
        "If dataGroup is not explicitly mentioned, leave it null. "
        "If variables_selected is not explicitly mentioned, leave it null."
    ),
)
def prepare_data_request(
    variables_selected: Optional[list[str]] = None,
    dataGroup: Optional[str] = None,
    time_phrase: Optional[str] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
    output_kind: Optional[str] = None,
) -> dict:
    normalized_vars = None
    if isinstance(variables_selected, list):
        cleaned = [str(v).strip().lower() for v in variables_selected if str(v).strip()]
        normalized_vars = cleaned or None

    normalized_group = None
    if isinstance(dataGroup, str) and dataGroup.strip():
        normalized_group = dataGroup.strip().lower()

    normalized_time_phrase = None
    if isinstance(time_phrase, str) and time_phrase.strip():
        normalized_time_phrase = time_phrase.strip()

    normalized_start = None
    if isinstance(start, str) and start.strip():
        normalized_start = start.strip()

    normalized_end = None
    if isinstance(end, str) and end.strip():
        normalized_end = end.strip()

    normalized_output_kind = None
    if isinstance(output_kind, str) and output_kind.strip():
        normalized_output_kind = output_kind.strip().lower()

    return {
        "kind": "pending_data_request",
        "variables_selected": normalized_vars,
        "dataGroup": normalized_group,
        "time_phrase": normalized_time_phrase,
        "start": normalized_start,
        "end": normalized_end,
        "output_kind": normalized_output_kind,
    }


def _mock_points(variables_selected: list[str], start: str, end: str) -> list[dict]:
    base = datetime(2026, 1, 1, 0, 0, 0)
    points = []
    for idx in range(6):
        row = {
            "timestamp": (base + timedelta(hours=idx)).isoformat(),
        }
        for var_index, variable in enumerate(variables_selected):
            row[variable] = round(18.5 + (idx * 0.7) + (var_index * 1.3), 2) # type: ignore
        points.append(row)
    return points


@tool(
    "get_timeseries",
    description=(
        "Fetch time-series station data. This is a mock tool that returns sample data. "
        "Provide variables_selected, dataGroup, start, and end."
    ),
)
def get_timeseries(
    variables_selected: list[str],
    dataGroup: str,
    start: str,
    end: str,
) -> dict:
    return {
        "mode": "mock",
        "kind": "timeseries",
        "variables_selected": [str(v).strip().lower() for v in variables_selected if str(v).strip()],
        "dataGroup": str(dataGroup).strip().lower(),
        "time_range": {"start": start, "end": end},
        "points": _mock_points(
            [str(v).strip().lower() for v in variables_selected if str(v).strip()],
            start,
            end,
        ),
    }


@tool(
    "make_chart",
    description=(
        "Create a chart-ready payload from station data. This is a mock tool that returns sample chart metadata. "
        "Provide variables_selected, dataGroup, start, and end."
    ),
)
def make_chart(
    variables_selected: list[str],
    dataGroup: str,
    start: str,
    end: str,
) -> dict:
    normalized_vars = [str(v).strip().lower() for v in variables_selected if str(v).strip()]
    return {
        "mode": "mock",
        "kind": "chart",
        "chart_type": "line",
        "title": f"Mock {' / '.join(normalized_vars) or 'station data'} chart",
        "variables_selected": normalized_vars,
        "dataGroup": str(dataGroup).strip().lower(),
        "time_range": {"start": start, "end": end},
        "points": _mock_points(normalized_vars, start, end),
    }


@tool(
    "make_table",
    description=(
        "Create a table-ready payload from station data. This is a mock tool that returns sample rows. "
        "Provide variables_selected, dataGroup, start, and end."
    ),
)
def make_table(
    variables_selected: list[str],
    dataGroup: str,
    start: str,
    end: str,
) -> dict:
    normalized_vars = [str(v).strip().lower() for v in variables_selected if str(v).strip()]
    return {
        "mode": "mock",
        "kind": "table",
        "columns": ["timestamp"] + normalized_vars,
        "variables_selected": normalized_vars,
        "dataGroup": str(dataGroup).strip().lower(),
        "time_range": {"start": start, "end": end},
        "rows": _mock_points(normalized_vars, start, end),
    }



STATION_TOOLS = [get_available_stations, set_station]
ALL_TOOLS = STATION_TOOLS  + [prepare_data_request]

REQUEST_TOOL_NAMES = {"prepare_data_request"}
OUTPUT_TYPE = ["chart", "table", "data"]