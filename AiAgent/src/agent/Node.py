from typing import Dict, List, Literal
from AiAgent.src.agent.State import State
from AiAgent.src.agent.Tools import get_available_stations, set_station
import json
import ast
from langgraph.prebuilt import ToolNode
from langchain_core.messages import BaseMessage, ToolMessage, AIMessage, SystemMessage

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

def route_after_model(state: State) -> Literal["end", "tools", "ask_for_station"]:
    last = state["messages"][-1]

    tool_calls = getattr(last, "tool_calls", None) or []
    if not tool_calls:
        return "end"

    station_id = state.get("station_id")

    if not station_id:
        for call in tool_calls:
            name = call.get("name")
            if name in DATA_TOOL_NAMES:
                return "ask_for_station"

    return "tools"

def ask_for_station(state: State) -> State:
    state["messages"].append(
        AIMessage(content="Pick a station first (type 'list stations' or search by name), then ask for charts/tables.")
    )
    return state

def _parse_tool_content(content):
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
