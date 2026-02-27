from typing import List
from datetime import datetime

from BackEnd.AiAgent.State import TimeRange
import json
import ast

from BackEnd.PostgreSQL.StationDbObject import StationDataGroup

def _verify_variables_selected(variables_selected: List[str] | None, stationMetadata : dict) -> tuple[bool, str | None]:
    if not variables_selected:
        return False, 'No variables are selected.'
    
    sensorsObj = stationMetadata.get("SensorsList")
    if not sensorsObj:
        return False, 'Available Station Sensors are not defined'
    
    availableSensors = []
    for sensor in sensorsObj:
        sensorName = sensor.get('sensor')
        if sensorName and str(sensorName).strip():
            availableSensors.append(sensorName.strip().lower())
    
    if not availableSensors:
        return False, "No readable sensor names found in station metadata."

    for var in variables_selected:
        v = var.strip().lower()
        if v not in availableSensors:
            allowed_preview = ", ".join(sorted(list(availableSensors)))
            return False, f"'{var}' is not an available sensor. Allowed: {allowed_preview}"
    return True, None


def _verify_timerange_entry(time_range: TimeRange | None) -> tuple[bool, str | None]:
    if time_range is None:
        return False, "time range is None"

    if not time_range.start or not time_range.end:
        return False, "time range must include both start and end"

    try:
        st = datetime.fromisoformat(time_range.start)
        end = datetime.fromisoformat(time_range.end)
    except ValueError:
        return False, "Invalid ISO date format for start or end."

    if st >= end:
        return False, "The end date must be after the start date"

    return True, None


def _verify_datagroup_entry(dataGroup: str | None) -> tuple[bool, str | None]:
    if dataGroup is None or not str(dataGroup).strip():
        return (False, "dataGroup is missing. Allowed: hourly/daily/weekly/monthly (or hour/day/week/month).")

    try:
        normalized = StationDataGroup.parse(dataGroup)
        return (True, normalized)
    except ValueError as e:
        return (False, str(e))






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