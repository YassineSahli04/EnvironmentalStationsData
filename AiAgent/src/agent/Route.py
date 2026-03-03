from typing import Dict, List, Literal, Optional

from agent.Tools import OUTPUT_TYPE
from agent.Helper import VerifState, _has_request_model_issue
from agent.State import State


def route_after_model(state: State) -> Literal['end', 'tools', 'ask_for_station']:
    last = state["messages"][-1]

    tool_calls = getattr(last, "tool_calls", None) or []
    if not tool_calls:
        return 'end'      

    return "tools"

def route_after_classify(state: State) -> Literal['call_model', 'ask_for_station', 'extract_data_request']:
    is_data_request = state.get('is_data_request')
    station_id = state.get('station_id')
 
    if is_data_request:
        if not station_id:
            return 'ask_for_station'
        return 'extract_data_request'
    
    return 'call_model'

def route_after_validation(state: State) -> Literal['try_resolve_data_entry_fields', 'ask_for_data_entry_field_update', 'ask_for_output_kind', 'execute_requested_tool']:
    validation_state = state.get('data_validation_status')
    is_data_entry_first_pass = True if state.get("is_data_entry_first_pass") else False 

    if validation_state == VerifState.Passed.value:
        output_kind = state.get("output_kind")
        if output_kind not in OUTPUT_TYPE:
            return "ask_for_output_kind"
        return "execute_requested_tool"

    elif is_data_entry_first_pass and validation_state == VerifState.RequestModel.value :
        return "try_resolve_data_entry_fields"    

    return "ask_for_data_entry_field_update"