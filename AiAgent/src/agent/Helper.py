from typing import List
from datetime import datetime
from enum import Enum
from BackEnd.AiAgent.State import TimeRange
import json
import ast
from BackEnd.PostgreSQL.StationDbObject import StationDataGroup

class VerifState(Enum):
    Passed= 'Passed';
    RequestModel= 'RequestModel';
    Failed= 'Failed';

def _extract_available_sensors(stationMetadata : dict) -> list[str]:
    sensorsObj = stationMetadata.get("SensorsList")
    availableSensors = []
    if sensorsObj:
        for sensor in sensorsObj:
            sensorName = sensor.get('sensor')
            if sensorName and str(sensorName).strip():
                availableSensors.append(sensorName.strip().lower())

    return sorted(set(availableSensors))

def _verify_variables_selected(variables_selected: List[str] | None, stationMetadata : dict) -> tuple[VerifState, str | None]:
    if not variables_selected:
        return VerifState.Failed, 'No variables are selected.'
    
    sensorsObj = stationMetadata.get("SensorsList")
    if not sensorsObj:
        return VerifState.Failed, 'Available Station Sensors are not defined. You should maybe look for an other station.'
    
    availableSensors = _extract_available_sensors(stationMetadata)
    
    if not availableSensors:
        return VerifState.Failed, "No readable sensor names found in station metadata. You should maybe look for an other station."

    requestModel = False
    verif_mess = ""
    for var in variables_selected:
        v = var.strip().lower()
        if v not in availableSensors:
            requestModel = True
            verif_mess += f"'{var}' is not an available sensor. "

    if requestModel:
        verif_mess += f'Allowed: {availableSensors}'
        return VerifState.RequestModel, verif_mess

    return VerifState.Passed, None


def _verify_timerange_entry(time_range: TimeRange | None) -> tuple[VerifState, str | None]:
    if time_range is None:
        return VerifState.Failed, "time range is None"

    if not time_range.start or not time_range.end:
        return VerifState.Failed, "time range must include both start and end"

    try:
        st = datetime.fromisoformat(time_range.start)
        end = datetime.fromisoformat(time_range.end)
    except ValueError:
        return VerifState.RequestModel, f"Invalid ISO date format for start or end. Start: {time_range.start}, End: {time_range.end}"

    if st >= end:
        return VerifState.Failed, "The end date must be after the start date"

    return VerifState.Passed, None


def _verify_datagroup_entry(dataGroup: str | None) -> tuple[VerifState, str | None]:
    if dataGroup is None or not str(dataGroup).strip():
        return (VerifState.Failed, "dataGroup is missing. Allowed: hourly/daily/weekly/monthly (or hour/day/week/month).")

    try:
        normalized = StationDataGroup.parse(dataGroup)
        return (VerifState.Passed, None)
    except ValueError as e:
        return (VerifState.RequestModel, str(e))






def _parse_tool_content(content):
    if isinstance(content, dict):
        return content
    if isinstance(content, str):
        s = content.strip()
        if not s:
            return {}
        try:
            return json.loads(s)
        except json.JSONDecodeError:
            try:
                val = ast.literal_eval(s)
                return val if isinstance(val, dict) else {"_raw": s}
            except Exception:
                return {"_raw": s}
    return {"_raw": str(content)}