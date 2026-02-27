from typing import Dict, List, Literal
from BackEnd.AiAgent.State import State
from BackEnd.AiAgent.Tools import get_available_stations, set_station
from langgraph.prebuilt import ToolNode
from langchain_core.messages import BaseMessage, ToolMessage, AIMessage, SystemMessage
from BackEnd.PostgreSQL.StationDbObject import StationDataGroup
from BackEnd.AiAgent.Helper import _parse_tool_content, _verify_datagroup_entry, _verify_timerange_entry, _verify_variables_selected, VerifState


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

def route_after_model(state: State) -> Literal["end", "tools", "ask_for_station", "validate_fields", "try_resolve_data_entry_fields", "ask_for_data_entry_field_update"]:
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
    metadata = state.get('station_meta')
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
                "data_entry_model_resolve_attempted" : True,
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
        
def ask_for_station(state: State) -> State:
    state["messages"].append(
        AIMessage(content="Pick a station first (type 'list stations' or search by name), then ask for charts/tables.")
    )
    return state

def validate_data_request(state: State) -> State:
    station_id = state.get("station_id")
    if not station_id:



