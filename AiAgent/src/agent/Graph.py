import os
from typing import Any

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph, END, START
from langfuse import Langfuse, get_client

from agent.McpTools import init_tool
from agent.Route import route_after_validation, route_after_classify, route_after_model
from agent.Node import ask_for_data_entry_field_update, ask_for_output_kind, ask_for_station, call_model, classify_intent, execute_chart_tool, execute_excel_export, execute_tools, extract_data_request, try_resolve_data_entry_fields, validate_fields, try_resolve_time_range
from agent.State import State
from langfuse.langchain import CallbackHandler
from agent.Logging import get_logger

logger = get_logger(__name__)


def _build_langfuse_handler() -> CallbackHandler | None:
    langfuse_pk_path = (os.getenv("LANGFUSE_PUBLIC_KEY_PATH") or "").strip()
    langfuse_sk_path = (os.getenv("LANGFUSE_SECRET_KEY_PATH") or "").strip()
    host = (os.getenv("LANGFUSE_HOST") or "").strip()

    if not langfuse_pk_path or not langfuse_sk_path:
        logger.info("[langfuse] disabled: LANGFUSE_PUBLIC_KEY_PATH and LANGFUSE_SECRET_KEY_PATH are required.")
        return None
    try:
        with open(langfuse_pk_path, "r", encoding="utf-8") as f:
            langfuse_pk = f.read().strip()
        with open(langfuse_sk_path, "r", encoding="utf-8") as f:
            langfuse_sk = f.read().strip()
    except Exception:
        logger.exception("[langfuse] disabled: failed to read credentials")
        return None

    if not langfuse_pk or not langfuse_sk:
        logger.warning("[langfuse] disabled: Langfuse keys are empty.")
        return None

    # In langfuse>=3, credentials belong to Langfuse client init.
    # CallbackHandler only accepts public_key for selecting the active client.
    try:
        if host:
            Langfuse(public_key=langfuse_pk, secret_key=langfuse_sk, host=host)
        else:
            Langfuse(public_key=langfuse_pk, secret_key=langfuse_sk)

        langfuse = get_client()

        # Verify connection
        if langfuse.auth_check():
            logger.info("Langfuse client is authenticated and ready")
        else:
            logger.warning("Langfuse authentication failed; disabling callbacks")
            return None
    except Exception:
        logger.exception("[langfuse] disabled: initialization/auth failed")
        return None
    
    logger.info("[langfuse] enabled (host=%s)", host or "default")
    return CallbackHandler(public_key=langfuse_pk)

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

    workflow.add_node("execute_chart_tool", execute_chart_tool)
    workflow.add_node("execute_excel_export", execute_excel_export)

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
            "classify_intent": "classify_intent"
        }
    )
    workflow.add_conditional_edges(
        "validate_fields", 
        route_after_validation, 
        {
            "try_resolve_data_entry_fields": "try_resolve_data_entry_fields",
            "ask_for_data_entry_field_update": "ask_for_data_entry_field_update",
            "ask_for_output_kind": "ask_for_output_kind",
            "execute_chart_tool": "execute_chart_tool",
            "execute_excel_export": "execute_excel_export",
        }
    )

    workflow.add_edge("execute_tools", "call_model")
    workflow.add_edge("extract_data_request", "validate_fields")
    workflow.add_edge("try_resolve_data_entry_fields", "try_resolve_time_range")
    workflow.add_edge("try_resolve_time_range", "validate_fields")
    workflow.add_edge("ask_for_station", END)
    workflow.add_edge("ask_for_output_kind", END)
    workflow.add_edge("ask_for_data_entry_field_update", END)
    workflow.add_edge("execute_chart_tool", END)
    workflow.add_edge("execute_excel_export", END)

    checkpointer = InMemorySaver()
    graph = workflow.compile(checkpointer=checkpointer)

    langfuse_handler = _build_langfuse_handler()
    if langfuse_handler:
        graph = graph.with_config({"callbacks": [langfuse_handler]})

    return graph

MCP_INITIALIZED = False

async def graph():
    global MCP_INITIALIZED

    if not MCP_INITIALIZED:
        await init_tool()
        MCP_INITIALIZED = True

    return build_graph()
