from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import InMemorySaver

from agent.Model import Model
from agent.NewNode import ask_for_station, call_model, classify_intent, execute_tools, route_after_classify, route_after_model, extract_data_request
from agent.State import State

SYSTEM = """
    You are a Meteorological Assistant.
    Keep answers short (max 2-3 sentences).

    Rules:
    1) If no station is locked, you must help the user list/search and then call set_station with an id.
    2) If station is locked, you can run data/visualization tools.
    3) Never invent station IDs or data; only use tool results.
"""

model = Model.build_default_model()

workflow = StateGraph(State)

workflow.add_node("classify_intent", classify_intent)
workflow.add_node("call_model", call_model)
workflow.add_node("extract_data_request", extract_data_request)
workflow.add_node("execute_tools", execute_tools)
workflow.add_node("ask_for_station", ask_for_station)

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
workflow.add_edge("execute_tools", "call_model")
workflow.add_edge("extract_data_request", END)
workflow.add_edge("ask_for_station", END)

# checkpointer = InMemorySaver()
testGraph = workflow.compile()
