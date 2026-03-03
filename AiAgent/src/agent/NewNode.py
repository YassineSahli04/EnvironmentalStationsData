from typing import Dict, List, Literal, Optional

from langchain_core.messages import AIMessage, BaseMessage, SystemMessage, ToolMessage, HumanMessage
from langgraph.prebuilt import ToolNode

from agent.Model import Model
from agent.State import ExtractedRequestResult, IntentResult, State, TimeRange
from agent.Tools import ALL_TOOLS, STATION_TOOLS
from agent.Helper import VerifState, _get_last_user_message_text, _parse_tool_content, _verify_datagroup_entry, _verify_timerange_entry, _verify_variables_selected

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

def call_model(state:State) -> Dict[str, List[BaseMessage]]:
    station_id = state.get("station_id")

    model_with_tools = model.bind_tools(STATION_TOOLS)

    prompt = f"""{SYSTEM}
        CURRENT STATION LOCKED: {station_id or "NONE"}"""

    response = model_with_tools.invoke(
        [SystemMessage(content=prompt)] + state["messages"]
    )
    return {"messages": [response]}

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
        "1. extracted_variables_selected:\n"
        "Write the result into the field named extracted_variables_selected.\n"
        "Extract only the actual requested measurement names or variables explicitly mentioned by the user.\n"
        "Examples: temperature, humidity, wind speed, rainfall.\n"
        "If the user does not explicitly name a variable, return null.\n"
        "\n"
        "2. extracted_dataGroup:\n"
        "Write the result into the field named extracted_dataGroup.\n"
        "This means the aggregation granularity of the data: how the data is grouped or concatenated over time.\n"
        "Typical examples are hourly, daily, weekly, monthly.\n"
        "Extract this only if the user explicitly names that grouping style.\n"
        "Do not infer a data group from a variable name.\n"
        "Do not confuse dataGroup with the sensor domain or category.\n"
        "Example: if the user says 'temperature data', that does NOT mean a dataGroup is provided.\n"
        "Example: 'daily temperature data' means dataGroup='daily'.\n"
        "If no data group is explicitly stated, return null.\n"
        "\n"
        "3. extracted_start and extracted_end:\n"
        "Write the values into the fields named extracted_start and extracted_end.\n"
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
        "4. extracted_output_kind:\n"
        "Write the result into the field named extracted_output_kind.\n"
        "Extract this only if the user explicitly asks for a presentation format.\n"
        "Examples: chart, graph, plot, table.\n"
        "If the user asks only to check or view data without naming a format, return null.\n"
        "\n"
        "Important examples:\n"
        "- 'I want to check the temp data' -> extracted_variables_selected=['temperature']; extracted_dataGroup=null; extracted_start=null; extracted_end=null; extracted_output_kind=null.\n"
        "- 'Show me a humidity chart for last week' -> extracted_variables_selected=['humidity']; extracted_dataGroup=null; extracted_start='last week'; extracted_end=null; extracted_output_kind='chart'.\n"
        "- 'Show daily temperature data from last week to today' -> extracted_variables_selected=['temperature']; extracted_dataGroup='daily'; extracted_start='last week'; extracted_end='today'; extracted_output_kind=null.\n"
        "- 'Give me weekly rainfall data from 2026-02-01 to 2026-02-07' -> extracted_variables_selected=['rainfall']; extracted_dataGroup='weekly'; extracted_start='2026-02-01'; extracted_end='2026-02-07'; extracted_output_kind=null.\n"
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

    raw_vars = extracted.extracted_variables_selected
    if isinstance(raw_vars, list):
        normalized_vars = [str(v).strip().lower() for v in raw_vars if str(v).strip()]
        if normalized_vars:
            updates["extracted_variables_selected"] = normalized_vars
            updates["variables_selected"] = normalized_vars

    if isinstance(extracted.extracted_dataGroup, str) and extracted.extracted_dataGroup.strip():
        normalized_group = extracted.extracted_dataGroup.strip().lower()
        updates["extracted_dataGroup"] = normalized_group
        updates["dataGroup"] = normalized_group

    if isinstance(extracted.extracted_output_kind, str) and extracted.extracted_output_kind.strip():
        normalized_output_kind = extracted.extracted_output_kind.strip().lower()
        updates["extracted_output_kind"] = normalized_output_kind
        updates["output_kind"] = normalized_output_kind

    start = extracted.extracted_start.strip() if isinstance(extracted.extracted_start, str) else None
    end = extracted.extracted_end.strip() if isinstance(extracted.extracted_end, str) else None
    if start:
        updates["extracted_start"] = start
    if end:
        updates["extracted_end"] = end
    if start or end:
        updates["time_range"] = TimeRange(start=start, end=end)

    return updates # type: ignore

def validate_fields(state: State) -> dict:
    is_data_entry_first_pass = False if state.get("is_data_entry_first_pass") else True 

    time_range = state.get("time_range")
    extracted_start_time = time_range.start if time_range and time_range.start else state.get("extracted_start")
    extracted_end_time = time_range.end if time_range and time_range.end else state.get("extracted_end")

    effective_variables_selected = state.get("variables_selected") or state.get("extracted_variables_selected")
    effective_dataGroup = state.get("dataGroup") or state.get("extracted_dataGroup")
    metadata = state.get("station_meta") or {}

    vars_verif, vars_mess = _verify_variables_selected(effective_variables_selected, metadata)
    time_verif, time_mess = _verify_timerange_entry(TimeRange(extracted_start_time, extracted_end_time))
    datagroup_verif, dataGroup_mess = _verify_datagroup_entry(effective_dataGroup)

    updates: dict = {}
    updates["time_range"] = TimeRange(extracted_start_time, extracted_end_time)
    updates["variables_selected"] = effective_variables_selected
    updates["dataGroup"] = effective_dataGroup

    request_model_issues = []
    failed_issues = []

    if vars_verif == VerifState.RequestModel:
        request_model_issues.append({"field":"variables_selected","reason":vars_mess})
    if vars_verif == VerifState.Failed:
        failed_issues.append({"field":"variables_selected","reason":vars_mess})
    if time_verif == VerifState.RequestModel:
        request_model_issues.append({"field":"time_range","reason":time_mess})
    if time_verif == VerifState.Failed:
        failed_issues.append({"field":"time_range","reason":time_mess})
    if datagroup_verif == VerifState.RequestModel:
        request_model_issues.append({"field":"dataGroup","reason":dataGroup_mess})
    if datagroup_verif == VerifState.Failed:
        failed_issues.append({"field":"dataGroup","reason":dataGroup_mess})

    if is_data_entry_first_pass and request_model_issues:
        updates.update({
            "is_data_entry_first_pass": True,
            "data_validation_status": VerifState.RequestModel.value,
            "data_validation_issues": request_model_issues,
        })
        return updates

    if failed_issues:
        updates.update({
            "data_entry_resolve_trial": False,
            "data_validation_status": VerifState.Failed.value,
            "data_validation_issues": failed_issues,
        })
        return updates
    
    updates.update({
        "data_entry_resolve_trial" : False,
        "data_validation_status": VerifState.Passed.value,
        "data_validation_issues": [],
    })
    return updates


        
