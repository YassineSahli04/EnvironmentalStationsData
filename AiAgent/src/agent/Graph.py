from langgraph.graph import END, START, StateGraph
from langgraph.checkpoint.memory import InMemorySaver

from typing import Any



from langgraph.graph import StateGraph, END, START

from agent.Route import route_after_validation, route_after_classify, route_after_model
from agent.Node import ask_for_data_entry_field_update, ask_for_output_kind, ask_for_station, call_model, classify_intent, execute_requested_tool, execute_tools, extract_data_request, try_resolve_data_entry_fields, validate_fields, try_resolve_time_range
from agent.State import State


def build_graph() -> Any:
    workflow = StateGraph(State)

    workflow.add_node("classify_intent", classify_intent)
    workflow.add_node("call_model", call_model)
    workflow.add_node("extract_data_request", extract_data_request)
    workflow.add_node("execute_tools", execute_tools)
    workflow.add_node("ask_for_station", ask_for_station)

    workflow.add_node("validate_fields", validate_fields)
    workflow.add_node("try_resolve_data_entry_fields", try_resolve_data_entry_fields)
    workflow.add_node("try_resolve_time_range", try_resolve_time_range)
    workflow.add_node("ask_for_data_entry_field_update", ask_for_data_entry_field_update)
    workflow.add_node("ask_for_output_kind", ask_for_output_kind)

    workflow.add_node("execute_requested_tool", execute_requested_tool)

    workflow.add_edge(START, "classify_intent")
    workflow.add_conditional_edges(
        "classify_intent", 
        route_after_classify, 
        {
            "call_model": "call_model",
            "extract_data_request": "extract_data_request",
            "ask_for_station": "ask_for_station"
        }
    )
    workflow.add_conditional_edges(
        "call_model", 
        route_after_model, 
        {
            "end": END,
            "tools": "execute_tools",
            "ask_for_station": "ask_for_station",
        }
    )
    workflow.add_conditional_edges(
        "validate_fields", 
        route_after_validation, 
        {
            "try_resolve_data_entry_fields": "try_resolve_data_entry_fields",
            "ask_for_data_entry_field_update": "ask_for_data_entry_field_update",
            "ask_for_output_kind": "ask_for_output_kind",
            "execute_requested_tool": "execute_requested_tool",
        }
    )

    workflow.add_edge("execute_tools", "call_model")
    workflow.add_edge("extract_data_request", "validate_fields")
    workflow.add_edge("try_resolve_data_entry_fields", "try_resolve_time_range")
    workflow.add_edge("try_resolve_time_range", "validate_fields")
    workflow.add_edge("ask_for_station", END)
    workflow.add_edge("ask_for_output_kind", END)
    workflow.add_edge("ask_for_data_entry_field_update", END)
    workflow.add_edge("execute_requested_tool", END)

    checkpointer = InMemorySaver()
    return workflow.compile(checkpointer=checkpointer)

def graph():
    return build_graph()
