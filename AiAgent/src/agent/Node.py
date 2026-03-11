from datetime import datetime
import asyncio
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List
from uuid import uuid4

from langchain_core.messages import AIMessage, BaseMessage, SystemMessage, ToolMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.prebuilt import ToolNode

from agent.McpTools import MCP_TOOLS
from agent.Model import Model
from agent.State import ExtractedRequestResult, IntentResult, State, TimeRange
from agent.Tools import ALL_TOOLS, OUTPUT_TYPE, STATION_TOOLS, get_station_data
from agent.Helper import StationDataGroup, VerifState, _extract_available_sensors, get_last_user_message_text, has_request_model_issue, parse_tool_content, verify_datagroup_entry, verify_timerange_entry, verify_variables_selected, transform_timeseries_to_excel_payload

model = Model.build_default_model()

SYSTEM = """
    You are a Meteorological Assistant.
    Keep answers short (max 2-3 sentences).

    Rules:
    1) If no station is locked, you must help the user list/search and then call set_station with an id.
    2) If station is locked, you can run data/visualization tools.
    3) Never invent station IDs or data; only use tool results.
"""

def classify_intent(state: State, config: RunnableConfig | None = None) -> Dict[str, bool]:
    last_msg = get_last_user_message_text(state)

    if not last_msg:
        return {"is_data_request": False, "recheck_intent": False}
    
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
        ],
        config=config,
    )
    if result.is_data_request and not state.get("station_id"):  # type: ignore
        return {"is_data_request": False, "recheck_intent": True} 

    return {"is_data_request": result.is_data_request, "recheck_intent": False} # type: ignore

def call_model(state:State, config: RunnableConfig | None = None) -> Dict[str, List[BaseMessage]]:
    station_id = state.get("station_id")
    station_meta = state.get('station_meta')
    is_data_request = bool(state.get("is_data_request"))

    if station_id and station_meta and is_data_request:
        model_with_tools = model.bind_tools(STATION_TOOLS + MCP_TOOLS)
    else:
        model_with_tools = model.bind_tools(STATION_TOOLS)

    prompt = f"""{SYSTEM}
        CURRENT STATION LOCKED: {station_id or "NONE"}"""

    response = model_with_tools.invoke(
        [SystemMessage(content=prompt)] + state["messages"],
        config=config,
    )
    return {"messages": [response]}

def execute_tools(state: State, config: RunnableConfig | None = None) -> State:
    tool_node = ToolNode(ALL_TOOLS + MCP_TOOLS)
    result = tool_node.invoke(state, config=config)

    for m in reversed(result["messages"]):
        if isinstance(m, ToolMessage) and m.name == 'set_station':
            payload = parse_tool_content(m.content)
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

def extract_data_request(state: State, config: RunnableConfig | None = None) -> State:
    last_msg = get_last_user_message_text(state)
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
        "Examples: chart, graph, plot, table, excel.\n"
        "If the user asks only to check or view data without naming a format, return null.\n"
        "\n"
        "Important examples:\n"
        "- 'I want to check the temp data' -> extracted_variables_selected=['temperature']; extracted_dataGroup=null; extracted_start=null; extracted_end=null; extracted_output_kind=null.\n"
        "- 'Show me a humidity chart for last week' -> extracted_variables_selected=['humidity']; extracted_dataGroup=null; extracted_start='last week'; extracted_end=null; extracted_output_kind='chart'.\n"
        "- 'Export the result to excel' -> extracted_variables_selected=null; extracted_dataGroup=null; extracted_start=null; extracted_end=null; extracted_output_kind='excel'.\n"
        "- 'Show daily temperature data from last week to today' -> extracted_variables_selected=['temperature']; extracted_dataGroup='daily'; extracted_start='last week'; extracted_end='today'; extracted_output_kind=null.\n"
        "- 'Give me weekly rainfall data from 2026-02-01 to 2026-02-07' -> extracted_variables_selected=['rainfall']; extracted_dataGroup='weekly'; extracted_start='2026-02-01'; extracted_end='2026-02-07'; extracted_output_kind=null.\n"
        "\n"
        "Return structured output only."
    )

    extracted = structured_model.invoke(
        [
            SystemMessage(content=prompt),
            HumanMessage(content=last_msg),
        ],
        config=config,
    )

    updates: dict = {}

    extracted_dict = getattr(extracted, "model_dump", lambda: extracted)()
    raw_vars = extracted_dict.get("extracted_variables_selected") # type: ignore
    if isinstance(raw_vars, list):
        normalized_vars = [str(v).strip().lower() for v in raw_vars if str(v).strip()]
        if normalized_vars:
            updates["extracted_variables_selected"] = normalized_vars

    data_group = extracted_dict.get("extracted_dataGroup") # type: ignore
    if isinstance(data_group, str) and data_group.strip():
        normalized_group = data_group.strip().lower()
        updates["extracted_dataGroup"] = normalized_group

    output_kind = extracted_dict.get("extracted_output_kind") # type: ignore
    if isinstance(output_kind, str) and output_kind.strip():
        normalized_output_kind = output_kind.strip().lower()
        updates["extracted_output_kind"] = normalized_output_kind

    start = extracted_dict.get("extracted_start") # type: ignore
    end = extracted_dict.get("extracted_end") # type: ignore
    start = start.strip() if isinstance(start, str) else None
    end = end.strip() if isinstance(end, str) else None
    if start:
        updates["extracted_start"] = start
    if end:
        updates["extracted_end"] = end

    return updates # type: ignore

def validate_fields(state: State) -> dict:
    is_data_entry_first_pass = False if state.get("is_data_entry_first_pass") else True 

    time_range = state.get("time_range")
    extracted_start_time = time_range.start if time_range and time_range.start else state.get("extracted_start")
    extracted_end_time = time_range.end if time_range and time_range.end else state.get("extracted_end")

    effective_variables_selected = state.get("variables_selected") or state.get("extracted_variables_selected")
    effective_dataGroup = state.get("dataGroup") or state.get("extracted_dataGroup")
    metadata = state.get("station_meta") or {}

    vars_verif, vars_mess = verify_variables_selected(effective_variables_selected, metadata)
    time_verif, time_mess = verify_timerange_entry(TimeRange(extracted_start_time, extracted_end_time))
    datagroup_verif, dataGroup_mess = verify_datagroup_entry(effective_dataGroup)

    updates: dict = {}
    updates["time_range"] = TimeRange(extracted_start_time, extracted_end_time)
    updates["variables_selected"] = effective_variables_selected
    updates["dataGroup"] = effective_dataGroup

    request_model_issues = []
    failed_issues = []

    if vars_verif == VerifState.RequestModel:
        request_model_issues.append({"field":"variables_selected","reason":vars_mess})
    if vars_verif == VerifState.Failed or (vars_verif == VerifState.RequestModel and not is_data_entry_first_pass):
        failed_issues.append({"field":"variables_selected","reason":vars_mess})
    if time_verif == VerifState.RequestModel:
        request_model_issues.append({"field":"time_range","reason":time_mess})
    if time_verif == VerifState.Failed or (time_verif == VerifState.RequestModel and not is_data_entry_first_pass):
        failed_issues.append({"field":"time_range","reason":time_mess})
    if datagroup_verif == VerifState.RequestModel:
        request_model_issues.append({"field":"dataGroup","reason":dataGroup_mess})
    if datagroup_verif == VerifState.Failed  or (datagroup_verif == VerifState.RequestModel and not is_data_entry_first_pass):
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
    
    
    extracted_output_kind = state.get('extracted_output_kind') or ""
    if extracted_output_kind.strip().lower() in OUTPUT_TYPE:
        updates.update({
            "output_kind": extracted_output_kind.strip().lower(),
            "extracted_output_kind": None
        })
        
    
    updates.update({
        "data_entry_resolve_trial" : False,
        "data_validation_status": VerifState.Passed.value,
        "data_validation_issues": [],
    })
    return updates

def try_resolve_data_entry_fields(state: State, config: RunnableConfig | None = None) -> dict:
    issues = state.get("data_validation_issues") or []
    if not any(has_request_model_issue(issues, field) for field in ("variables_selected", "dataGroup")):
        return {}
    
    metadata = state.get("station_meta") or {}
    available_sensors = _extract_available_sensors(metadata)

    payload = {
        "issues": issues,
        "current": {
            "variables_selected": state.get("variables_selected"),
            "dataGroup": state.get("dataGroup"),
            "time_range": {
                "start": state.get("time_range").start if state.get("time_range") else None,  # type: ignore
                "end": state.get("time_range").end if state.get("time_range") else None,  # type: ignore
            },
        },
        "constraints": {
            "allowed_sensors": available_sensors,
        },
    }

    resolver_prompt = (
        "Resolve only obvious typos/format issues.\n"
        "Never invent values outside constraints.\n"
        "Return ONLY valid JSON with keys: "
        "{\"variables_selected\": list|null, \"dataGroup\": str|null}. "
        "Use null for fields you cannot safely resolve."
    )

    response = model.invoke(
        [
            SystemMessage(content=resolver_prompt),
            HumanMessage(content=json.dumps(payload)),
        ],
        config=config,
    )
    model_data = parse_tool_content(getattr(response, "content", ""))

    updates: dict = {"data_entry_model_resolve_attempted": True}

    candidate_vars = model_data.get("variables_selected") if isinstance(model_data, dict) else None
    if isinstance(candidate_vars, list) and candidate_vars and available_sensors:
        normalized_vars = [str(v).strip().lower() for v in candidate_vars if str(v).strip()]
        if normalized_vars and all(v in available_sensors for v in normalized_vars):
            updates["variables_selected"] = normalized_vars

    candidate_group = model_data.get("dataGroup") if isinstance(model_data, dict) else None
    if isinstance(candidate_group, str) and candidate_group.strip():
        try:
            updates["dataGroup"] = StationDataGroup.parse(candidate_group)
        except ValueError:
            pass

    return updates
    
def try_resolve_time_range(state: State, config: RunnableConfig | None = None) -> dict:
    issues = state.get("data_validation_issues") or []
    if not has_request_model_issue(issues, "time_range"):
        return {}
    current_range = state.get("time_range")

    payload = {
        "issues": [issue for issue in (issues) if isinstance(issue, dict) and issue.get("field") == "time_range"],
        "current_time_range": {
            "start": current_range.start if current_range else None,  # type: ignore
            "end": current_range.end if current_range else None,  # type: ignore
        },
        "current_datetime": datetime.now().isoformat(),
    }

    resolver_prompt = (
        "Resolve only the time_range field.\n"
        "Convert relative date phrases like today, yesterday, last week, and last month into concrete ISO 8601 datetimes.\n"
        "Use the current system datetime provided by the caller as the reference.\n"
        "Return ONLY valid JSON with this shape: "
        "{\"time_range\": {\"start\": str|null, \"end\": str|null}|null}. "
        "If you cannot safely resolve it, return {\"time_range\": null}."
    )

    response = model.invoke(
        [
            SystemMessage(content=resolver_prompt),
            HumanMessage(content=json.dumps(payload)),
        ],
        config=config,
    )

    model_data = parse_tool_content(getattr(response, "content", ""))
    updates: dict = {}

    candidate_range = model_data.get("time_range") if isinstance(model_data, dict) else None
    if isinstance(candidate_range, dict):
        st_raw = candidate_range.get("start")
        end_raw = candidate_range.get("end")
        if isinstance(st_raw, str) and isinstance(end_raw, str):
            try:
                st = st_raw.strip()
                end = end_raw.strip()
                if st and end:
                    parsed_start = datetime.fromisoformat(st)
                    parsed_end = datetime.fromisoformat(end)
                    if parsed_start < parsed_end:
                        updates["time_range"] = TimeRange(start=st, end=end)
            except ValueError:
                pass

    return updates

def ask_for_data_entry_field_update(state: State) -> State:
    issues = state.get("data_validation_issues") or []

    if not issues:
        msg = "Please update your request fields (variables, time range, or data group)."
    else:
        failed_reasons = []
        for issue in issues:
            if isinstance(issue, dict):
                field = issue.get("field")
                if field:
                    state[field] = None
                reason = issue.get("reason")
                if field and reason:
                    failed_reasons.append(f"{field}: {reason}")
        sections = []
        if failed_reasons:
            sections.append("Failed checks: " + "; ".join(failed_reasons))
        msg = "Please update your request. " + " | ".join(sections)
    state["messages"].append(AIMessage(content=msg))
    state["is_data_entry_first_pass"] = False
    state["data_validation_issues"] = []
    state["data_validation_status"] = None

    state["extracted_variables_selected"] = None
    state["extracted_dataGroup"] = None
    state["extracted_start"] = None
    state["extracted_end"] = None

    return state

def ask_for_output_kind(state: State) -> State:
    options = ", ".join(OUTPUT_TYPE)
    message = (
        "Pick how you want the output. "
        f"Choose one of: {options}."
    )

    state["messages"].append(
        AIMessage(content=message)
    )
    return state


async def execute_excel_export(state: State, config: RunnableConfig | None = None) -> State:
    station_id = state.get('station_id')
    sensors = state.get('variables_selected')
    dataGroup = state.get('dataGroup')
    time_range = state.get('time_range')

    station_data = []
    if station_id and sensors and dataGroup and time_range and time_range.start and time_range.end:
        station_data = await asyncio.to_thread(
            get_station_data, station_id, sensors, dataGroup, time_range.start, time_range.end
        )

    default_export_dir = Path(__file__).resolve().parents[2] / "output"
    export_dir = Path(os.getenv("EXPORT_DIR", str(default_export_dir)))
    export_dir.mkdir(parents=True, exist_ok=True)

    thread_id = "anonymous"
    if isinstance(config, dict):
        configurable = config.get("configurable")
        if isinstance(configurable, dict):
            raw_thread_id = configurable.get("thread_id")
            if isinstance(raw_thread_id, str) and raw_thread_id.strip():
                thread_id = raw_thread_id.strip()

    safe_thread_id = re.sub(r"[^A-Za-z0-9._-]", "_", thread_id)[:80] or "anonymous"
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%S%fZ")
    unique_suffix = uuid4().hex[:8]
    file_name = f"out_{safe_thread_id}_{timestamp}_{unique_suffix}.xlsx"
    output_path = str(export_dir / file_name)
    sheet_name = "Data"

    payload = transform_timeseries_to_excel_payload(
        rows=station_data, # type: ignore
        file_path=output_path,
        sheet=sheet_name,
    )

    write_tool = next(
        (
            tool
            for tool in MCP_TOOLS
            if str(getattr(tool, "name", "")).strip() == "write_file"
            or str(getattr(tool, "name", "")).strip().endswith("write_file")
        ),
        None,
    )
    if write_tool is None:
        return {
            "messages": [AIMessage(content="Excel export failed because the MCP write tool is not available.")],
        } # type: ignore

    try:
        await write_tool.ainvoke(payload, config=config) # type: ignore[arg-type]
    except Exception as exc:
        return {
            "messages": [AIMessage(content=f"Excel export failed: {str(exc)}")],
        } # type: ignore

    return {
        "output_kind": None,
        "messages": [AIMessage(content=f"Excel export created, please click to download it.",
                               additional_kwargs={
                                    "file_path": output_path,
                                }
    )],
    } # type: ignore

async def execute_chart_tool(state: State, config: RunnableConfig | None = None) -> State:
    station_id = state.get('station_id')
    sensors = state.get('variables_selected')
    dataGroup = state.get('dataGroup')
    time_range = state.get('time_range')

    station_data = []
    if station_id and sensors and dataGroup and time_range and time_range.start and time_range.end:
        station_data = await asyncio.to_thread(
            get_station_data, station_id, sensors, dataGroup, time_range.start, time_range.end
        )

    if not MCP_TOOLS:
        return {
            "station_data": station_data,
            "messages": [AIMessage(content="No MCP tools are available right now.")],
        } # type: ignore

    payload = {
        "station_id": station_id,
        "variables_selected": sensors,
        "dataGroup": dataGroup,
        "start": time_range.start if time_range else None, # type: ignore
        "end": time_range.end if time_range else None, # type: ignore
        "output_kind": state.get("output_kind"),
        "rows": station_data,
    }

    model_with_mcp = model.bind_tools(MCP_TOOLS)
    ai = await model_with_mcp.ainvoke([
        SystemMessage(content=(
            "You are a data-visualization planner for meteorological data. "
            "Call exactly one MCP visualization tool and use only fields from the provided payload. "
            "Do not invent fields or values.\n"
            "\n"
            "Chart quality requirements:\n"
            "- Prefer a clean, minimal chart with high readability.\n"
            "- Keep titles concise and informative.\n"
            "- Format numeric values to 1-2 decimals max.\n"
            "- Avoid dense value labels on every point; show labels only when necessary.\n"
            "- Use a subtle grid and strong contrast for the main series.\n"
            "- Keep axis labels short and human-friendly.\n"
            "- Avoid overlapping text and clutter.\n"
            "- If dates are dense, reduce x-axis tick density for readability.\n"
            "- Use a neutral background and a professional palette.\n"
            "\n"
            "Output target:\n"
            "- If output_kind is chart, generate a clean line chart optimized for readability.\n"
            "- If output_kind is table or data, choose the matching visualization/tool behavior.\n"
            "\n"
            "Return a tool call only."
        )),
        HumanMessage(content=json.dumps(payload)),
    ], config=config)

    result = await ToolNode(MCP_TOOLS).ainvoke({"messages": [ai]}, config=config)
    tool_messages = [m for m in result.get("messages", []) if isinstance(m, ToolMessage)]
    if tool_messages:
        last_tool = tool_messages[-1]
        is_chart_output = str(state.get("output_kind") or "").strip().lower() == "chart"
        chart_reset = {
            "time_range": None,
            "variables_selected": None,
            "dataGroup": None,
            "output_kind": None,
            "station_data": None,
        } if is_chart_output else {"station_data": station_data}

        return {
            **chart_reset,
            "messages": [ai, last_tool, AIMessage(content=f"Visualization generated with tool '{last_tool.text}'.")],
        } # type: ignore

    return {
        "station_data": station_data,
        "messages": [ai, AIMessage(content="No MCP tool execution result was returned.")],
    } # type: ignore
