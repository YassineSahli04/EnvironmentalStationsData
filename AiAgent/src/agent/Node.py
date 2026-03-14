import calendar
from datetime import datetime
import asyncio
import json
import os
import re
from pathlib import Path
from typing import Dict, List
from uuid import uuid4

from langchain_core.messages import AIMessage, BaseMessage, SystemMessage, ToolMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.prebuilt import ToolNode

from agent.McpTools import MCP_TOOLS
from agent.Logging import get_logger
from agent.Model import Model
from agent.State import ExtractedRequestResult, IntentResult, State, TimeRange
from agent.Tools import ALL_TOOLS, OUTPUT_TYPE, STATION_TOOLS, get_station_data
from agent.Helper import StationDataGroup, VerifState, _extract_available_sensors, get_last_user_messages, has_request_model_issue, parse_tool_content, verify_datagroup_entry, verify_timerange_entry, verify_variables_selected, transform_timeseries_to_excel_payload, sanitize_iso_datetime

model = Model.build_default_model()
logger = get_logger(__name__)

SYSTEM = """
    You are a Meteorological Assistant.
    Keep answers short (max 2-3 sentences).

    Rules:
    1) If no station is locked, you must help the user list/search and then call set_station with an id.
    2) If station is locked, you can run data/visualization tools.
    3) Never invent station IDs or data; only use tool results.
"""

def classify_intent(state: State, config: RunnableConfig | None = None) -> Dict[str, bool]:
    msgs = get_last_user_messages(state, 5)

    if not msgs:
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

    messages: list[BaseMessage] = [SystemMessage(content=prompt)]

    if len(msgs) > 4:
        messages.append(HumanMessage(content=msgs[4]))
    
    if len(msgs) > 3:
        messages.append(HumanMessage(content=msgs[3]))
    
    if len(msgs) > 2:
        messages.append(HumanMessage(content=msgs[2]))
    
    if len(msgs) > 1:
        messages.append(HumanMessage(content=msgs[1]))

    if len(msgs) > 0:
        messages.append(HumanMessage(content=msgs[0]))
    try:
        result = structured_model.invoke(
            messages,
            config=config,
        )
    except Exception:
        logger.exception("classify_intent failed")
        return {"is_data_request": False, "recheck_intent": False}
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

    try:
        response = model_with_tools.invoke(
            [SystemMessage(content=prompt)] + state["messages"],
            config=config,
        )
    except Exception:
        logger.exception("call_model failed")
        return {
            "messages": [
                AIMessage(content="I hit an internal error while generating a response. Please try again.")
            ]
        }
    return {"messages": [response]}

def execute_tools(state: State, config: RunnableConfig | None = None) -> State:
    tool_node = ToolNode(ALL_TOOLS + MCP_TOOLS)
    try:
        result = tool_node.invoke(state, config=config)
    except Exception:
        logger.exception("execute_tools failed")
        return {
            "messages": [
                AIMessage(content="A tool execution failed. Please try again or adjust your request.")
            ]
        } # type: ignore

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
    msg = get_last_user_messages(state)
    last_msg = msg[0]
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
        "3. extracted_time_phrase, extracted_start, and extracted_end:\n"
        "Write time values into the correct fields: extracted_time_phrase, extracted_start, extracted_end.\n"
        "Use extracted_start and extracted_end only for explicit range boundaries.\n"
        "Use extracted_time_phrase for a single standalone time phrase without explicit boundaries.\n"
        "Copy the user's wording as-is. Do not convert to date format in this step.\n"
        "Time values can be exact dates, datetimes, or natural-language expressions.\n"
        "Range examples:\n"
        "- from 2026-02-01 to 2026-02-07 -> extracted_start='2026-02-01', extracted_end='2026-02-07', extracted_time_phrase=null.\n"
        "- from last week to today -> extracted_start='last week', extracted_end='today', extracted_time_phrase=null.\n"
        "- between yesterday and this morning -> extracted_start='yesterday', extracted_end='this morning', extracted_time_phrase=null.\n"
        "Standalone phrase examples (no explicit start/end words):\n"
        "- this month -> extracted_time_phrase='this month', extracted_start=null, extracted_end=null.\n"
        "- for last week -> extracted_time_phrase='last week', extracted_start=null, extracted_end=null.\n"
        "- today -> extracted_time_phrase='today', extracted_start=null, extracted_end=null.\n"
        "Single explicit date/datetime without a range boundary goes to extracted_start.\n"
        "Example: on 2026-02-01 -> extracted_start='2026-02-01', extracted_end=null, extracted_time_phrase=null.\n"
        "If both a standalone phrase and explicit range boundaries appear, prioritize boundaries for extracted_start/extracted_end and set extracted_time_phrase=null.\n"
        "\n"
        "4. extracted_output_kind:\n"
        "Write the result into the field named extracted_output_kind.\n"
        "Extract this only if the user explicitly asks for a presentation format.\n"
        "Examples: chart, graph, plot, table, excel.\n"
        "If the user asks only to check or view data without naming a format, return null.\n"
        "\n"
        "Important examples:\n"
        "- 'I want to check the temp data' -> extracted_variables_selected=['temperature']; extracted_dataGroup=null; extracted_time_phrase=null; extracted_start=null; extracted_end=null; extracted_output_kind=null.\n"
        "- 'Show me a humidity chart for this month' -> extracted_variables_selected=['humidity']; extracted_dataGroup=null; extracted_time_phrase='this month'; extracted_start=null; extracted_end=null; extracted_output_kind='chart'.\n"
        "- 'Export the result to excel' -> extracted_variables_selected=null; extracted_dataGroup=null; extracted_time_phrase=null; extracted_start=null; extracted_end=null; extracted_output_kind='excel'.\n"
        "- 'Show daily temperature data from last week to today' -> extracted_variables_selected=['temperature']; extracted_dataGroup='daily'; extracted_time_phrase=null; extracted_start='last week'; extracted_end='today'; extracted_output_kind=null.\n"
        "- 'Give me weekly rainfall data from 2026-02-01 to 2026-02-07' -> extracted_variables_selected=['rainfall']; extracted_dataGroup='weekly'; extracted_time_phrase=null; extracted_start='2026-02-01'; extracted_end='2026-02-07'; extracted_output_kind=null.\n"
        "\n"
        "Return structured output only."
    )

    try:
        extracted = structured_model.invoke(
            [
                SystemMessage(content=prompt),
                HumanMessage(content=last_msg),
            ],
            config=config,
        )
    except Exception:
        logger.exception("extract_data_request failed")
        return {} # type: ignore

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

    time_phrase = extracted_dict.get("extracted_time_phrase") # type: ignore
    time_phrase = time_phrase.strip() if isinstance(time_phrase, str) else None
    updates["extracted_time_phrase"] = time_phrase

    start = extracted_dict.get("extracted_start") # type: ignore
    end = extracted_dict.get("extracted_end") # type: ignore
    start = start.strip() if isinstance(start, str) else None
    end = end.strip() if isinstance(end, str) else None
    if start:
        updates["extracted_start"] = start
    if end:
        updates["extracted_end"] = end

    updates["is_data_entry_first_pass"] = None
    updates["data_validation_status"] = None
    updates["data_validation_issues"] = None
    return updates # type: ignore

def validate_fields(state: State) -> dict:
    is_data_entry_first_pass = False if state.get("is_data_entry_first_pass") else True 

    extracted_time_phrase = state.get("extracted_time_phrase")
    time_range = state.get("time_range")
    if not time_range:
        time_range = TimeRange(None, None)
    extracted_start = state.get("extracted_start")
    extracted_end = state.get("extracted_end")

    updates: dict = {}
    
    if extracted_time_phrase and not extracted_start and not extracted_end:
        extracted_start_time = None
        extracted_end_time = None
        time_verif, time_mess = VerifState.RequestModel, "Time format should be: From start To end."
    else:
        extracted_start_time = extracted_start if extracted_start else time_range.start
        extracted_end_time = extracted_end if extracted_end else time_range.end
        time_verif, time_mess = verify_timerange_entry(TimeRange(extracted_start_time, extracted_end_time))        
        updates["time_range"] = TimeRange(extracted_start_time, extracted_end_time)

    effective_variables_selected = state.get("extracted_variables_selected") or state.get("variables_selected")
    effective_dataGroup = state.get("extracted_dataGroup") or state.get("dataGroup")
    metadata = state.get("station_meta") or {}

    vars_verif, vars_mess = verify_variables_selected(effective_variables_selected, metadata) 
    datagroup_verif, dataGroup_mess = verify_datagroup_entry(effective_dataGroup)

    
    updates["variables_selected"] = effective_variables_selected
    updates["dataGroup"] = effective_dataGroup

    updates["extracted_variables_selected"] = None
    updates["extracted_dataGroup"] = None
    updates["extracted_start"] = None
    updates["extracted_end"] = None

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

        extracted_output_kind = state.get('extracted_output_kind') or ""
    
    extracted_output_kind = state.get('extracted_output_kind') or ""
    if extracted_output_kind.strip().lower() in OUTPUT_TYPE:
        updates.update({
            "output_kind": extracted_output_kind.strip().lower(),
            "extracted_output_kind": None
        })
    
    if is_data_entry_first_pass and request_model_issues:
        updates.update({
            "is_data_entry_first_pass": True,
            "data_validation_status": VerifState.RequestModel.value,
            "data_validation_issues": request_model_issues,
        })
        return updates

    if failed_issues:
        updates.update({
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

    try:
        response = model.invoke(
            [
                SystemMessage(content=resolver_prompt),
                HumanMessage(content=json.dumps(payload)),
            ],
            config=config,
        )
    except Exception:
        logger.exception("try_resolve_data_entry_fields failed")
        return {"data_entry_model_resolve_attempted": True}
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
    current_time_phrase = state.get("extracted_time_phrase")

    payload = {
        "issues": [issue for issue in (issues) if isinstance(issue, dict) and issue.get("field") == "time_range"],
        "current_time_range": {
            "start": current_range.start if current_range else None,  # type: ignore
            "end": current_range.end if current_range else None,  # type: ignore
        },
        "current_time_phrase": current_time_phrase,
        "current_datetime": datetime.now().isoformat(),
    }

    resolver_prompt = (
        "Convert relative date phrases (today, yesterday, last week, last month, etc.) "
        "into concrete ISO-8601 datetimes.\n"
        "Use the provided current_datetime as the reference.\n\n"

        "STRICT VALIDATION RULES:\n"
        "- Returned datetimes MUST be valid calendar dates.\n"
        "- February has 28 days except on leap years (29 days).\n"
        "- Leap year rule: divisible by 4, but centuries must also be divisible by 400.\n"
        "- Months must respect their correct day count (30 or 31).\n"
        "- If a computed date would be invalid, adjust it to the "
        "closest valid date.\n\n"

        "OUTPUT RULES:\n"
        "- Always return valid ISO-8601 timestamps: YYYY-MM-DDTHH:MM:SS.\n"
        "- Return ONLY valid JSON.\n"
        "- JSON shape must be exactly:\n"
        "{\"time_range\": {\"start\": str|null, \"end\": str|null}|null}\n"
        "- If the phrase cannot be safely resolved, return {\"time_range\": null}."
    )

    try:
        response = model.invoke(
            [
                SystemMessage(content=resolver_prompt),
                HumanMessage(content=json.dumps(payload)),
            ],
            config=config,
        )
    except Exception:
        logger.exception("try_resolve_time_range failed")
        return {}

    model_data = parse_tool_content(getattr(response, "content", ""))
    updates: dict = {}

    candidate_range = model_data.get("time_range") if isinstance(model_data, dict) else None
    if isinstance(candidate_range, dict):
        st_raw = candidate_range.get("start")
        end_raw = candidate_range.get("end")
        if isinstance(st_raw, str) and isinstance(end_raw, str):
            st = sanitize_iso_datetime(st_raw)
            end = sanitize_iso_datetime(end_raw)
            if st and end:
                try:
                    start_dt = datetime.fromisoformat(st.replace("Z", "+00:00"))
                    end_dt = datetime.fromisoformat(end.replace("Z", "+00:00"))
                    if start_dt <= end_dt:
                        updates["time_range"] = TimeRange(start=st, end=end)
                        updates["extracted_time_phrase"] = None
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
                reason = issue.get("reason")
                if field and reason:
                    failed_reasons.append(f"{field}: {reason}")
        sections = []
        if failed_reasons:
            sections.append("Failed checks: " + "; ".join(failed_reasons))
        msg = "Please update your request. " + " | ".join(sections)
    state["messages"].append(AIMessage(content=msg))

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
    try:
        if station_id and sensors and dataGroup and time_range and time_range.start and time_range.end:
            station_data = await asyncio.to_thread(
                get_station_data, station_id, sensors, dataGroup, time_range.start, time_range.end
            )
    except Exception:
        logger.exception("execute_excel_export data fetch failed")
        return {
            "messages": [AIMessage(content="Excel export failed while fetching station data.")],
        } # type: ignore

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
        logger.exception("execute_excel_export write_file failed")
        return {
            "messages": [AIMessage(content=f"Excel export failed: {str(exc)}")],
        } # type: ignore

    return {
        "messages": [AIMessage(content=f"Excel export created, please check the file.",
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
    try:
        if station_id and sensors and dataGroup and time_range and time_range.start and time_range.end:
            station_data = await asyncio.to_thread(
                get_station_data, station_id, sensors, dataGroup, time_range.start, time_range.end
            )
    except Exception:
        logger.exception("execute_chart_tool data fetch failed")
        return {
            "messages": [AIMessage(content="Visualization failed while fetching station data.")],
        } # type: ignore

    if not MCP_TOOLS:
        return {
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

    try:
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
    except Exception:
        logger.exception("execute_chart_tool failed")
        return {
            "messages": [AIMessage(content="Visualization generation failed. Please try again.")],
        } # type: ignore
    tool_messages = [m for m in result.get("messages", []) if isinstance(m, ToolMessage)]
    if tool_messages:
        last_tool = tool_messages[-1]
        return {
            "messages": [ai, last_tool, AIMessage(content=f"Visualization generated with tool '{last_tool.text}'.")],
        } # type: ignore

    return {
        "messages": [ai, AIMessage(content="No MCP tool execution result was returned.")],
    } # type: ignore
