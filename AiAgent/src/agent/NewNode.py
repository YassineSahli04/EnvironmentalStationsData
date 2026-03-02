from typing import Dict, List, Literal, Optional

from langchain_core.messages import AIMessage, BaseMessage, SystemMessage, ToolMessage, HumanMessage
from langgraph.prebuilt import ToolNode

from agent.Model import Model
from agent.State import ExtractedRequestResult, IntentResult, State, TimeRange
from agent.Tools import ALL_TOOLS, STATION_TOOLS
from agent.Helper import _get_last_user_message_text, _parse_tool_content

tool_node = ToolNode(ALL_TOOLS)
model = Model.build_default_model()

SYSTEM = """
    You are a Meteorological Assistant.
    Keep answers short (max 2-3 sentences).

    Rules:
    1) If no station is locked, you must help the user list/search and then call set_station with an id.
    2) If station is locked, you can run data/visualization tools.
    3) Never invent station IDs or data; only use tool results.
"""

def classify_intent(state: State) -> Dict[str, bool]:
    last_msg = _get_last_user_message_text(state)

    if not last_msg:
        return {"is_data_request": False}
    
    structured_model = model.with_structured_output(IntentResult)

    prompt = (
            "Classify whether the user's message is an explicit data request.\n"
            "\n"
            "Set is_data_request=true only when the user explicitly asks to get, see, inspect, analyze, plot, graph, chart, or tabulate data values.\n"
            "A request is also an explicit data request if the user clearly names one or more variables to analyze, such as temperature, humidity, wind speed, or rainfall, optionally with a time constraint.\n"
            "The request for data must be explicit.\n"
            "Do not mark it as true just because the user mentions a station, says 'analyze the station', or speaks generally about weather.\n"
            "\n"
            "Set is_data_request=false for station lookup, station listing, station search, station selection, general chat, vague requests, or requests that do not explicitly ask for data values.\n"
            "\n"
            "Examples:\n"
            "- 'show temperature data' -> true\n"
            "- 'plot humidity for last week' -> true\n"
            "- 'I want to analyze temperature' -> true\n"
            "- 'list stations' -> false\n"
            "- 'find a station in Toronto' -> false\n"
            "- 'analyze this station' -> false\n"
            "\n"
            "Do not infer hidden intent. Classify only what the user explicitly asked."
        )

    result = structured_model.invoke(
        [
            SystemMessage(content=prompt),
            HumanMessage(content=last_msg),
        ]
    )

    return {"is_data_request": result.is_data_request} # type: ignore

def route_after_classify(state: State) -> Literal['call_model', 'ask_for_station', 'extract_data_request']:
    is_data_request = state.get('is_data_request')
    station_id = state.get('station_id')
 
    if is_data_request:
        if not station_id:
            return 'ask_for_station'
        return 'extract_data_request'
    
    return 'call_model'

def call_model(state:State) -> Dict[str, List[BaseMessage]]:
    station_id = state.get("station_id")

    model_with_tools = model.bind_tools(STATION_TOOLS)

    prompt = f"""{SYSTEM}
        CURRENT STATION LOCKED: {station_id or "NONE"}"""

    response = model_with_tools.invoke(
        [SystemMessage(content=prompt)] + state["messages"]
    )
    return {"messages": [response]}

def route_after_model(state: State) -> Literal['end', 'tools', 'ask_for_station']:
    last = state["messages"][-1]

    tool_calls = getattr(last, "tool_calls", None) or []
    if not tool_calls:
        return 'end'      

    return "tools"

def execute_tools(state: State) -> State:
    result = tool_node.invoke(state)

    for m in reversed(result["messages"]):
        if isinstance(m, ToolMessage) and m.name == 'set_station':
            payload = _parse_tool_content(m.content)
            station_id = payload.get("Id")
            
            result["station_id"] = str(station_id) if station_id is not None else None  # type: ignore
            result["station_meta"] = payload
            break
    return result

def ask_for_station(state: State) -> State:
    state["messages"].append(
        AIMessage(content="Pick a station first (type 'list stations' or search by name), then ask for charts/tables.")
    )
    return state

def extract_data_request(state: State) -> State:
    last_msg = _get_last_user_message_text(state)
    if not last_msg:
        return {} # type: ignore

    structured_model = model.with_structured_output(ExtractedRequestResult)
    prompt = (
        "You are extracting structured request fields from one user message.\n"
        "Your job is extraction only, not interpretation, planning, or completion.\n"
        "\n"
        "Follow these priorities in order:\n"
        "1. Copy only what the user explicitly says.\n"
        "2. Put each value in the correct field.\n"
        "3. Leave anything missing as null.\n"
        "4. Never convert, expand, or guess values.\n"
        "\n"
        "Return values only when the user explicitly states them.\n"
        "If the user does not clearly state a field, return null for that field.\n"
        "Do not guess missing values.\n"
        "Do not infer a likely value from context.\n"
        "Do not complete partial requests.\n"
        "Do not choose defaults.\n"
        "\n"
        "Field rules:\n"
        "1. variables_selected:\n"
        "Extract only the actual requested measurement names or variables explicitly mentioned by the user.\n"
        "Examples: temperature, humidity, wind speed, rainfall.\n"
        "If the user does not explicitly name a variable, return null.\n"
        "\n"
        "2. dataGroup:\n"
        "This means the aggregation granularity of the data: how the data is grouped or concatenated over time.\n"
        "Typical examples are hourly, daily, weekly, monthly.\n"
        "Extract this only if the user explicitly names that grouping style.\n"
        "Do not infer a data group from a variable name.\n"
        "Do not confuse dataGroup with the sensor domain or category.\n"
        "Example: if the user says 'temperature data', that does NOT mean a dataGroup is provided.\n"
        "Example: 'daily temperature data' means dataGroup='daily'.\n"
        "If no data group is explicitly stated, return null.\n"
        "\n"
        "3. start and end:\n"
        "Use these for any explicit time constraint stated by the user.\n"
        "Copy the user's wording as-is into the correct side of the range.\n"
        "The values do NOT need to be in date format.\n"
        "They can be exact dates, datetimes, or natural-language expressions.\n"
        "Examples: from 2026-02-01 to 2026-02-07 -> start='2026-02-01', end='2026-02-07'.\n"
        "Examples: from last week to today -> start='last week', end='today'.\n"
        "Examples: between yesterday and this morning -> start='yesterday', end='this morning'.\n"
        "If the user gives only one explicit time expression, put it in start and leave end null.\n"
        "Examples: for last week -> start='last week', end=null.\n"
        "Examples: on 2026-02-01 -> start='2026-02-01', end=null.\n"
        "Do not convert relative phrases into dates in this step.\n"
        "\n"
        "4. output_kind:\n"
        "Extract this only if the user explicitly asks for a presentation format.\n"
        "Examples: chart, graph, plot, table.\n"
        "If the user asks only to check or view data without naming a format, return null.\n"
        "\n"
        "Important examples:\n"
        "- 'I want to check the temp data' -> variables_selected=['temperature']; dataGroup=null; start=null; end=null; output_kind=null.\n"
        "- 'Show me a humidity chart for last week' -> variables_selected=['humidity']; dataGroup=null; start='last week'; end=null; output_kind='chart'.\n"
        "- 'Show daily temperature data from last week to today' -> variables_selected=['temperature']; dataGroup='daily'; start='last week'; end='today'; output_kind=null.\n"
        "- 'Give me weekly rainfall data from 2026-02-01 to 2026-02-07' -> variables_selected=['rainfall']; dataGroup='weekly'; start='2026-02-01'; end='2026-02-07'; output_kind=null.\n"
        "\n"
        "Return structured output only."
    )

    extracted = structured_model.invoke(
        [
            SystemMessage(content=prompt),
            HumanMessage(content=last_msg),
        ]
    )

    updates: dict = {}

    raw_vars = extracted.variables_selected # type: ignore
    if isinstance(raw_vars, list):
        normalized_vars = [str(v).strip().lower() for v in raw_vars if str(v).strip()]
        if normalized_vars:
            updates["variables_selected"] = normalized_vars

    if isinstance(extracted.dataGroup, str) and extracted.dataGroup.strip(): # type: ignore
        updates["dataGroup"] = extracted.dataGroup.strip() # type: ignore

    if isinstance(extracted.output_kind, str) and extracted.output_kind.strip(): # type: ignore
        updates["output_kind"] = extracted.output_kind.strip().lower() # type: ignore

    start = extracted.start.strip() if isinstance(extracted.start, str) else None # type: ignore
    end = extracted.end.strip() if isinstance(extracted.end, str) else None # type: ignore
    if start or end:
        updates["time_range"] = TimeRange(start=start, end=end)

    return updates # type: ignore


        
