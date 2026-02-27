from typing import Dict, List, Literal
from datetime import datetime
import json
from BackEnd.AiAgent.State import State, TimeRange
from BackEnd.AiAgent.Tools import get_available_stations, set_station
from langgraph.prebuilt import ToolNode
from langchain_core.messages import BaseMessage, ToolMessage, AIMessage, SystemMessage, HumanMessage
from BackEnd.PostgreSQL.StationDbObject import StationDataGroup
from BackEnd.AiAgent.Helper import _parse_tool_content, _verify_datagroup_entry, _verify_timerange_entry, _verify_variables_selected, VerifState, _extract_available_sensors


STATION_TOOLS = [get_available_stations, set_station]
DATA_TOOLS = []
ALL_TOOLS = STATION_TOOLS + DATA_TOOLS

tool_node = ToolNode(ALL_TOOLS)

DATA_TOOL_NAMES = {"get_timeseries", "make_chart", "make_table"} 

def call_model_factory(model, system_prompt: str):
    """
    Returns a call_model(state) function bound to your llm.
    We bind tools dynamically: if station not locked, only station tools are bound.
    """
    def call_model(state: State) -> Dict[str, List[BaseMessage]]:
        station_id = state.get("station_id")
        tools = STATION_TOOLS if not station_id else ALL_TOOLS
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
        if name in DATA_TOOL_NAMES:
            if not station_id:
                return "ask_for_station"
            return "validate_fields"          

    return "tools"

def route_after_validate(state: State) -> Literal["tools", "try_resolve_data_entry_fields", "ask_for_data_entry_field_update"]:
    status = state.get("data_validation_status")
    attempted = state.get("data_entry_model_resolve_attempted", False)

    if status == VerifState.Passed.value:
        return "tools"
    if status == VerifState.RequestModel.value and not attempted:
        return "try_resolve_data_entry_fields"
    return "ask_for_data_entry_field_update"

def validate_fields(state: State) -> dict:
    time_range = state.get("time_range")
    variables_selected = state.get('variables_selected')
    dataGroup = state.get('dataGroup')
    metadata = state.get('station_meta') or {}
    data_entry_model_resolve_attempted = state.get("data_entry_model_resolve_attempted")


    vars_verif, vars_mess = _verify_variables_selected(variables_selected, metadata) # type: ignore
    time_verif, time_mess = _verify_timerange_entry(time_range)
    datagroup_verif, dataGroup_mess = _verify_datagroup_entry(dataGroup)

    if not data_entry_model_resolve_attempted or data_entry_model_resolve_attempted == False:
        if vars_verif == VerifState.RequestModel or time_verif == VerifState.RequestModel or datagroup_verif == VerifState.RequestModel:
            data_validation_issues = []
            if vars_verif == VerifState.RequestModel:
                data_validation_issues.append({"field":"variables_selected","reason":vars_mess})
            if time_verif == VerifState.RequestModel:
                data_validation_issues.append({"field":"time_range","reason":time_mess})
            if datagroup_verif == VerifState.RequestModel:
                data_validation_issues.append({"field":"dataGroup","reason":dataGroup_mess})

            return {
                "data_validation_status": VerifState.RequestModel.value,
                "data_validation_issues": data_validation_issues,
            }


    if vars_verif == VerifState.Failed or time_verif == VerifState.Failed or datagroup_verif == VerifState.Failed:
        data_validation_issues = []
        if vars_verif == VerifState.Failed:
            data_validation_issues.append({"field":"variables_selected","reason":vars_mess})
        if time_verif == VerifState.Failed:
            data_validation_issues.append({"field":"time_range","reason":time_mess})
        if datagroup_verif == VerifState.Failed:
            data_validation_issues.append({"field":"dataGroup","reason":dataGroup_mess})
        return {
            "data_entry_model_resolve_attempted" : False,
            "data_validation_status": VerifState.Failed.value,
            "data_validation_issues": data_validation_issues,
        }
    
    return {
        "data_entry_model_resolve_attempted" : False,
        "data_validation_status": VerifState.Passed.value,
        "data_validation_issues": [],
    }


def try_resolve_data_entry_fields_factory(model):
    def try_resolve_data_entry_fields(state: State) -> dict:
        issues = state.get("data_validation_issues") or []
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
            "{\"variables_selected\": list|null, \"dataGroup\": str|null, "
            "\"time_range\": {\"start\": str|null, \"end\": str|null}|null}. "
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

        candidate_range = model_data.get("time_range") if isinstance(model_data, dict) else None
        if isinstance(candidate_range, dict):
            st_raw = candidate_range.get("start")
            end_raw = candidate_range.get("end")
            if isinstance(st_raw, str) and isinstance(end_raw, str):
                try:
                    st = datetime.fromisoformat(st_raw.strip())
                    end = datetime.fromisoformat(end_raw.strip())
                    if st < end:
                        updates["time_range"] = TimeRange(start=st_raw.strip(), end=end_raw.strip())
                except ValueError:
                    pass

        return updates
    return try_resolve_data_entry_fields

def ask_for_data_entry_field_update(state: State) -> State:
    issues = state.get("data_validation_issues") or []
    if not issues:
        msg = "Please update your request fields (variables, time range, or data group)."
    else:
        reasons = []
        for issue in issues:
            if isinstance(issue, dict):
                field = issue.get("field")
                reason = issue.get("reason")
                if field and reason:
                    reasons.append(f"{field}: {reason}")
        msg = "I couldn't safely auto-correct some fields. Please update: " + "; ".join(reasons)
    state["messages"].append(AIMessage(content=msg))
    return state
        
def ask_for_station(state: State) -> State:
    state["messages"].append(
        AIMessage(content="Pick a station first (type 'list stations' or search by name), then ask for charts/tables.")
    )
    return state



