from typing import Dict, List, Literal
from datetime import datetime
import json
from agent.State import State, TimeRange
from agent.Tools import get_available_stations, get_timeseries, make_chart, make_table, prepare_data_request, set_station
from langgraph.prebuilt import ToolNode
from langchain_core.messages import BaseMessage, ToolMessage, AIMessage, SystemMessage, HumanMessage
from agent.Helper import _parse_tool_content, _verify_datagroup_entry, _verify_timerange_entry, _verify_variables_selected, VerifState, _extract_available_sensors, StationDataGroup


STATION_TOOLS = [get_available_stations, set_station]
DATA_TOOLS = [get_timeseries, make_chart, make_table]
ALL_TOOLS = STATION_TOOLS + DATA_TOOLS + [prepare_data_request]

tool_node = ToolNode(ALL_TOOLS)

DATA_TOOL_NAMES = {"get_timeseries", "make_chart", "make_table"} 
REQUEST_TOOL_NAMES = {"prepare_data_request"}


def _extract_pending_data_request(state: State) -> dict:
    last = state["messages"][-1]
    tool_calls = getattr(last, "tool_calls", None) or []

    for call in tool_calls:
        name = call.get("name")
        if name not in REQUEST_TOOL_NAMES:
            continue

        args = call.get("args")
        if not isinstance(args, dict):
            continue

        extracted: dict = {}

        raw_vars = args.get("variables_selected")
        if isinstance(raw_vars, list):
            normalized_vars = [str(v).strip().lower() for v in raw_vars if str(v).strip()]
            if normalized_vars:
                extracted["variables_selected"] = normalized_vars

        raw_group = args.get("dataGroup")
        if isinstance(raw_group, str) and raw_group.strip():
            extracted["dataGroup"] = raw_group.strip()

        raw_start = args.get("start")
        raw_end = args.get("end")
        if isinstance(raw_start, str) and raw_start.strip() and isinstance(raw_end, str) and raw_end.strip():
            extracted["time_range"] = TimeRange(start=raw_start.strip(), end=raw_end.strip())

        return extracted

    return {}

def call_model_factory(model, system_prompt: str):
    """
    Returns a call_model(state) function bound to your llm.
    We bind tools dynamically: if station not locked, only station tools are bound.
    """
    def call_model(state: State) -> Dict[str, List[BaseMessage]]:
        station_id = state.get("station_id")
        tools = STATION_TOOLS if not station_id else STATION_TOOLS + [prepare_data_request]
        model_with_tools = model.bind_tools(tools)

        prompt = f"""{system_prompt}
            CURRENT STATION LOCKED: {station_id or "NONE"}"""

        response = model_with_tools.invoke(
            [SystemMessage(content=prompt)] + state["messages"]
        )
        return {"messages": [response]}
    return call_model

def execute_tools(state: State) -> State:
    result = tool_node.invoke(state)

    for m in reversed(result["messages"]):
        if isinstance(m, ToolMessage) and m.name == "set_station":
            payload = _parse_tool_content(m.content)
            station_id = payload.get("Id") # type: ignore
            result["station_id"] = str(station_id) if station_id is not None else None  # type: ignore
            result["station_meta"] = payload
            break

    return result

def route_after_model(state: State) -> Literal["end", "tools", "ask_for_station", "validate_fields"]:
    last = state["messages"][-1]

    tool_calls = getattr(last, "tool_calls", None) or []
    if not tool_calls:
        return "end"

    station_id = state.get("station_id")

    for call in tool_calls:
        name = call.get("name")
        if name in REQUEST_TOOL_NAMES:
            if not station_id:
                return "ask_for_station"
            return "validate_fields"          

    return "tools"

def _has_request_model_issue(issues: list[dict], field_name: str) -> bool:
    for issue in issues:
        if isinstance(issue, dict) and issue.get("field") == field_name:
            return True
    return False


def route_after_validate(state: State) -> Literal["tools", "try_resolve_time_range", "try_resolve_data_entry_fields", "ask_for_data_entry_field_update"]:
    status = state.get("data_validation_status")
    issues = state.get("data_validation_request_model_issues") or []
    data_attempted = state.get("data_entry_model_resolve_attempted", False)
    time_attempted = state.get("time_range_model_resolve_attempted", False)

    if status == VerifState.Passed.value:
        return "tools"
    if status != VerifState.RequestModel.value:
        return "ask_for_data_entry_field_update"

    if _has_request_model_issue(issues, "time_range") and not time_attempted:
        return "try_resolve_time_range"
    if any(_has_request_model_issue(issues, field) for field in ("variables_selected", "dataGroup")) and not data_attempted:
        return "try_resolve_data_entry_fields"
    return "ask_for_data_entry_field_update"

def validate_fields(state: State) -> dict:
    extracted_request = _extract_pending_data_request(state)

    time_range = extracted_request.get("time_range") or state.get("time_range")
    variables_selected = extracted_request.get("variables_selected") or state.get("variables_selected")
    dataGroup = extracted_request.get("dataGroup") or state.get("dataGroup")
    metadata = state.get('station_meta') or {}
    vars_verif, vars_mess = _verify_variables_selected(variables_selected, metadata) # type: ignore
    time_verif, time_mess = _verify_timerange_entry(time_range)
    datagroup_verif, dataGroup_mess = _verify_datagroup_entry(dataGroup)

    updates: dict = {}
    if "time_range" in extracted_request:
        updates["time_range"] = time_range
    if "variables_selected" in extracted_request:
        updates["variables_selected"] = variables_selected
    if "dataGroup" in extracted_request:
        updates["dataGroup"] = dataGroup

    request_model_issues = []
    failed_issues = []

    if vars_verif == VerifState.RequestModel:
        request_model_issues.append({"field":"variables_selected","reason":vars_mess})
    if vars_verif == VerifState.Failed:
        failed_issues.append({"field":"variables_selected","reason":vars_mess})
    if time_verif == VerifState.RequestModel:
        request_model_issues.append({"field":"time_range","reason":time_mess})
    if time_verif == VerifState.Failed:
        failed_issues.append({"field":"time_range","reason":time_mess})
    if datagroup_verif == VerifState.RequestModel:
        request_model_issues.append({"field":"dataGroup","reason":dataGroup_mess})
    if datagroup_verif == VerifState.Failed:
        failed_issues.append({"field":"dataGroup","reason":dataGroup_mess})

    if request_model_issues:
        updates.update({
            "data_validation_status": VerifState.RequestModel.value,
            "data_validation_request_model_issues": request_model_issues,
            "data_validation_failed_issues": failed_issues,
        })
        return updates

    if failed_issues:
        updates.update({
            "data_entry_model_resolve_attempted" : False,
            "time_range_model_resolve_attempted": False,
            "data_validation_status": VerifState.Failed.value,
            "data_validation_request_model_issues": [],
            "data_validation_failed_issues": failed_issues,
        })
        return updates
    
    updates.update({
        "data_entry_model_resolve_attempted" : False,
        "time_range_model_resolve_attempted": False,
        "data_validation_status": VerifState.Passed.value,
        "data_validation_request_model_issues": [],
        "data_validation_failed_issues": [],
    })
    return updates


def try_resolve_time_range_factory(model):
    def try_resolve_time_range(state: State) -> dict:
        current_range = state.get("time_range")

        payload = {
            "issues": [issue for issue in (state.get("data_validation_request_model_issues") or []) if isinstance(issue, dict) and issue.get("field") == "time_range"],
            "current_time_range": {
                "start": current_range.start if current_range else None,  # type: ignore
                "end": current_range.end if current_range else None,  # type: ignore
            },
            "current_datetime": datetime.now().isoformat(),
        }

        resolver_prompt = (
            "Resolve only the time_range field.\n"
            "Convert relative date phrases like today, yesterday, last week, and last month into concrete ISO 8601 datetimes.\n"
            "Use the current system datetime provided by the caller as the reference.\n"
            "Return ONLY valid JSON with this shape: "
            "{\"time_range\": {\"start\": str|null, \"end\": str|null}|null}. "
            "If you cannot safely resolve it, return {\"time_range\": null}."
        )

        response = model.invoke(
            [
                SystemMessage(content=resolver_prompt),
                HumanMessage(content=json.dumps(payload)),
            ]
        )

        model_data = _parse_tool_content(getattr(response, "content", ""))
        updates: dict = {"time_range_model_resolve_attempted": True}

        candidate_range = model_data.get("time_range") if isinstance(model_data, dict) else None
        if isinstance(candidate_range, dict):
            st_raw = candidate_range.get("start")
            end_raw = candidate_range.get("end")
            if isinstance(st_raw, str) and isinstance(end_raw, str):
                try:
                    st = st_raw.strip()
                    end = end_raw.strip()
                    if st and end:
                        parsed_start = datetime.fromisoformat(st)
                        parsed_end = datetime.fromisoformat(end)
                        if parsed_start < parsed_end:
                            updates["time_range"] = TimeRange(start=st, end=end)
                except ValueError:
                    pass

        return updates
    return try_resolve_time_range


def try_resolve_data_entry_fields_factory(model):
    def try_resolve_data_entry_fields(state: State) -> dict:
        issues = state.get("data_validation_request_model_issues") or []
        metadata = state.get("station_meta") or {}
        available_sensors = _extract_available_sensors(metadata)

        payload = {
            "issues": issues,
            "current": {
                "variables_selected": state.get("variables_selected"),
                "dataGroup": state.get("dataGroup"),
                "time_range": {
                    "start": state.get("time_range").start if state.get("time_range") else None,  # type: ignore
                    "end": state.get("time_range").end if state.get("time_range") else None,  # type: ignore
                },
            },
            "constraints": {
                "allowed_sensors": available_sensors,
            },
        }

        resolver_prompt = (
            "Resolve only obvious typos/format issues.\n"
            "Never invent values outside constraints.\n"
            "Return ONLY valid JSON with keys: "
            "{\"variables_selected\": list|null, \"dataGroup\": str|null}. "
            "Use null for fields you cannot safely resolve."
        )

        response = model.invoke(
            [
                SystemMessage(content=resolver_prompt),
                HumanMessage(content=json.dumps(payload)),
            ]
        )
        model_data = _parse_tool_content(getattr(response, "content", ""))

        updates: dict = {"data_entry_model_resolve_attempted": True}

        candidate_vars = model_data.get("variables_selected") if isinstance(model_data, dict) else None
        if isinstance(candidate_vars, list) and candidate_vars and available_sensors:
            normalized_vars = [str(v).strip().lower() for v in candidate_vars if str(v).strip()]
            if normalized_vars and all(v in available_sensors for v in normalized_vars):
                updates["variables_selected"] = normalized_vars

        candidate_group = model_data.get("dataGroup") if isinstance(model_data, dict) else None
        if isinstance(candidate_group, str) and candidate_group.strip():
            try:
                updates["dataGroup"] = StationDataGroup.parse(candidate_group)
            except ValueError:
                pass

        return updates
    return try_resolve_data_entry_fields

def ask_for_data_entry_field_update(state: State) -> State:
    failed_issues = state.get("data_validation_failed_issues") or []
    unresolved_request_model_issues = state.get("data_validation_request_model_issues") or []

    if not failed_issues and not unresolved_request_model_issues:
        msg = "Please update your request fields (variables, time range, or data group)."
    else:
        failed_reasons = []
        unresolved_reasons = []
        for issue in failed_issues:
            if isinstance(issue, dict):
                field = issue.get("field")
                reason = issue.get("reason")
                if field and reason:
                    failed_reasons.append(f"{field}: {reason}")
        for issue in unresolved_request_model_issues:
            if isinstance(issue, dict):
                field = issue.get("field")
                reason = issue.get("reason")
                if field and reason:
                    unresolved_reasons.append(f"{field}: {reason}")
        sections = []
        if failed_reasons:
            sections.append("Failed checks: " + "; ".join(failed_reasons))
        if unresolved_reasons:
            sections.append("Could not auto-resolve: " + "; ".join(unresolved_reasons))
        msg = "Please update your request. " + " | ".join(sections)
    state["messages"].append(AIMessage(content=msg))
    state["data_entry_model_resolve_attempted"] = False
    state["time_range_model_resolve_attempted"] = False
    return state
        

def ask_for_station(state: State) -> State:
    state["messages"].append(
        AIMessage(content="Pick a station first (type 'list stations' or search by name), then ask for charts/tables.")
    )
    return state


