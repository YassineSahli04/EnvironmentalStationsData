from langgraph.graph import END, START, StateGraph
from langchain_core.language_models import BaseChatModel
from langgraph.checkpoint.memory import InMemorySaver

from typing import Any



from agent.Node import (
    ask_for_station,
    call_model_factory,
    execute_tools,
    route_after_model,
    validate_fields,
    route_after_validate,
    try_resolve_time_range_factory,
    try_resolve_data_entry_fields_factory,
    ask_for_data_entry_field_update,
)
from agent.State import State
from agent.Model import Model



def _trace_node(name: str, fn):
    def traced(*args, **kwargs):
        print(f"[node] {name}", flush=True)
        return fn(*args, **kwargs)

    return traced

def build_graph(model : BaseChatModel) -> Any:
    SYSTEM = """
        You are a Meteorological Assistant.
        Keep answers short (max 2-3 sentences).

        Rules:
        1) If no station is locked, you must help the user list/search and then call set_station with an id.
        2) If station is locked, you can run data/visualization tools.
        3) Never invent station IDs or data; only use tool results.
    """

    workflow = StateGraph(State)

    workflow.add_node("call_model", _trace_node("call_model", call_model_factory(model, SYSTEM)))
    workflow.add_node("execute_tools", _trace_node("execute_tools", execute_tools))
    workflow.add_node("ask_for_station", _trace_node("ask_for_station", ask_for_station))
    workflow.add_node("validate_fields", _trace_node("validate_fields", validate_fields))
    workflow.add_node(
        "try_resolve_time_range",
        _trace_node("try_resolve_time_range", try_resolve_time_range_factory(model)),
    )
    workflow.add_node(
        "try_resolve_data_entry_fields",
        _trace_node("try_resolve_data_entry_fields", try_resolve_data_entry_fields_factory(model)),
    )
    workflow.add_node(
        "ask_for_data_entry_field_update",
        _trace_node("ask_for_data_entry_field_update", ask_for_data_entry_field_update),
    )

    workflow.add_edge(START, "call_model")

    workflow.add_conditional_edges(
        "call_model",
        route_after_model,
        {
            "end": END,
            "tools": "execute_tools",
            "ask_for_station": "ask_for_station",
            "validate_fields": "validate_fields",
        },
    )

    workflow.add_conditional_edges(
        "validate_fields",
        route_after_validate,
        {
            "tools": "execute_tools",
            "try_resolve_time_range": "try_resolve_time_range",
            "try_resolve_data_entry_fields": "try_resolve_data_entry_fields",
            "ask_for_data_entry_field_update": "ask_for_data_entry_field_update",
        },
    )

    # Loop: after tools, go back to model
    workflow.add_edge("execute_tools", "call_model")
    workflow.add_edge("try_resolve_time_range", "validate_fields")
    workflow.add_edge("try_resolve_data_entry_fields", "validate_fields")

    # If we asked for station, end the turn
    workflow.add_edge("ask_for_station", END)
    workflow.add_edge("ask_for_data_entry_field_update", END)

    checkpointer = InMemorySaver()
    return workflow.compile(checkpointer=checkpointer)

def graph():
    return build_graph(Model.build_default_model())
