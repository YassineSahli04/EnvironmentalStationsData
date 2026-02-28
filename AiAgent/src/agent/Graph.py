from langgraph.graph import END, START, StateGraph
from typing import Any

from agent.Node import (
    ask_for_station,
    call_model_factory,
    execute_tools,
    route_after_model,
    validate_fields,
    route_after_validate,
    try_resolve_data_entry_fields_factory,
    ask_for_data_entry_field_update,
)
from agent.State import State
from langgraph.checkpoint.memory import InMemorySaver

def build_graph(model) -> Any:
    SYSTEM = """
        You are a Meteorological Assistant.
        Keep answers short (max 2-3 sentences).

        Rules:
        1) If no station is locked, you must help the user list/search and then call set_station with an id.
        2) If station is locked, you can run data/visualization tools.
        3) Never invent station IDs or data; only use tool results.
    """

    graph = StateGraph(State)

    graph.add_node("call_model", call_model_factory(model, SYSTEM))
    graph.add_node("execute_tools", execute_tools)
    graph.add_node("ask_for_station", ask_for_station)
    graph.add_node("validate_fields", validate_fields)
    graph.add_node("try_resolve_data_entry_fields", try_resolve_data_entry_fields_factory(model))
    graph.add_node("ask_for_data_entry_field_update", ask_for_data_entry_field_update)

    graph.add_edge(START, "call_model")

    graph.add_conditional_edges(
        "call_model",
        route_after_model,
        {
            "end": END,
            "tools": "execute_tools",
            "ask_for_station": "ask_for_station",
            "validate_fields": "validate_fields",
        },
    )

    graph.add_conditional_edges(
        "validate_fields",
        route_after_validate,
        {
            "tools": "execute_tools",
            "try_resolve_data_entry_fields": "try_resolve_data_entry_fields",
            "ask_for_data_entry_field_update": "ask_for_data_entry_field_update",
        },
    )

    # Loop: after tools, go back to model
    graph.add_edge("execute_tools", "call_model")
    graph.add_edge("try_resolve_data_entry_fields", "validate_fields")

    # If we asked for station, end the turn
    graph.add_edge("ask_for_station", END)
    graph.add_edge("ask_for_data_entry_field_update", END)

    checkpointer = InMemorySaver()
    return graph.compile(checkpointer=checkpointer)
