import calendar
import re

from langchain_core.messages import HumanMessage

from agent.State import State, TimeRange

from typing import Any, List, Optional
from datetime import date, datetime, time
from enum import Enum
import json
import ast

class StationDataGroup(Enum):
    hourly= 'hour'
    daily =  'day'
    weekly= 'week'
    monthly = 'month'

    @classmethod
    def parse(cls, raw: object) -> str:
        if isinstance(raw, cls):
            return raw.value
        if isinstance(raw, str):
            s = raw.strip().lower()

            if s in cls.__members__:
                return cls.__members__[s].value

            for e in cls:
                if e.value == s:
                    return e.value
            
        allowed_names = list(cls.__members__.keys())
        allowed_values = [e.value for e in cls]
        raise ValueError(
            f"Invalid dataGroup {raw!r}. "
            f"Allowed names: {allowed_names}. Allowed values: {allowed_values}."
        )

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

def verify_variables_selected(variables_selected: List[str] | None, stationMetadata : dict) -> tuple[VerifState, str | None]:
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

def verify_timerange_entry(time_range: TimeRange | None) -> tuple[VerifState, str | None]:
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

def verify_datagroup_entry(dataGroup: str | None) -> tuple[VerifState, str | None]:
    if dataGroup is None or not str(dataGroup).strip():
        return (VerifState.Failed, "dataGroup is missing. Allowed: hourly/daily/weekly/monthly (or hour/day/week/month).")

    try:
        normalized = StationDataGroup.parse(dataGroup)
        return (VerifState.Passed, None)
    except ValueError as e:
        return (VerifState.RequestModel, str(e))

def has_request_model_issue(issues: list[dict], field_name: str) -> bool:
    for issue in issues:
        if isinstance(issue, dict) and issue.get("field") == field_name:
            return True
    return False

def get_last_user_messages(state: State, number_messages:int = 1) -> List[str]:
    msgs = []
    for msg in reversed(state["messages"]):
        if isinstance(msg, HumanMessage):
            content = getattr(msg, "content", None)
            if isinstance(content, str) and content.strip():
                msgs.append(content.strip())
                if len(msgs) == number_messages:
                    return msgs
    return msgs

def parse_tool_content(content):
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

def transform_timeseries_to_excel_payload(
    rows: list[dict[str, Any]],
    file_path: str,
    sheet: str = "Data",
    time_key: str = "time",
    values_key: str = "values",
) -> dict[str, Any]:
    def _cell(value: Any) -> Any:
        if value is None:
            return ""
        if isinstance(value, (datetime, date, time)):
            return value.isoformat()
        if isinstance(value, (str, int, float, bool)):
            return value
        try:
            return json.dumps(value, ensure_ascii=False)
        except TypeError:
            return str(value)

    if not isinstance(rows, list) or not rows:
        return {
            "filePath": file_path,
            "sheet": sheet,
            "headers": [],
            "data": [],
        }
    
    headers = [time_key] + list(rows[0][values_key].keys())

    formatted_rows = []
    for row in rows:
        values = row.get(values_key, {})
        row_values = [_cell(row.get(time_key))] + [_cell(values.get(k)) for k in headers[1:]]
        formatted_rows.append(row_values)

    return {
        "filePath": file_path,
        "sheet": sheet,
        "headers": headers,
        "data": formatted_rows,
    }

def sanitize_iso_datetime(value: str) -> str | None:
    raw = value.strip()
    if not raw:
        return None

    has_z = raw.endswith("Z")
    candidate = raw[:-1] if has_z else raw

    try:
        parsed = datetime.fromisoformat(candidate)
        normalized = parsed.isoformat(timespec="seconds")
        return f"{normalized}Z" if has_z else normalized
    except ValueError:
        pass

    match = re.match(
        r"^(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})"
        r"[T\s](?P<hour>\d{2}):(?P<minute>\d{2})(?::(?P<second>\d{2}))?$",
        candidate,
    )
    if not match:
        return None

    year = int(match.group("year"))
    month = int(match.group("month"))
    day = int(match.group("day"))
    hour = int(match.group("hour"))
    minute = int(match.group("minute"))
    second = int(match.group("second") or "00")

    if month < 1 or month > 12:
        return None
    if hour > 23 or minute > 59 or second > 59:
        return None

    max_day = calendar.monthrange(year, month)[1]
    safe_day = min(max(day, 1), max_day)

    try:
        repaired = datetime(year, month, safe_day, hour, minute, second)
    except ValueError:
        return None

    normalized = repaired.isoformat(timespec="seconds")
    return f"{normalized}Z" if has_z else normalized

