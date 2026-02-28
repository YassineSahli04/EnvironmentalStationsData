from langgraph.graph import END, START, StateGraph
from typing import Any

from AiAgent.src.agent.Node import ask_for_station, call_model_factory, execute_tools, route_after_model
from AiAgent.src.agent.State import State
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

    graph.add_edge(START, "call_model")

    graph.add_conditional_edges(
        "call_model",
        route_after_model,
        {
            "end": END,
            "tools": "execute_tools",
            "ask_for_station": "ask_for_station",
        },
    )

    # Loop: after tools, go back to model
    graph.add_edge("execute_tools", "call_model")

    # If we asked for station, end the turn
    graph.add_edge("ask_for_station", END)

    checkpointer = InMemorySaver()
    return graph.compile(checkpointer=checkpointer)
