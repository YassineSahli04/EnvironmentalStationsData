from fastapi import FastAPI
from pydantic import BaseModel
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from pathlib import Path
import ast
import base64
import json
import mimetypes
import re
from agent.Graph import build_graph
from agent.McpTools import init_tool

app = FastAPI()
graph = build_graph()


@app.on_event("startup")
async def startup_event():
    await init_tool()

class ChatRequest(BaseModel):
    message: str
    thread_id: str


def _parse_content(value: object) -> dict:
    if isinstance(value, dict):
        return value
    if not isinstance(value, str):
        return {}

    raw = value.strip()
    if not raw:
        return {}

    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, dict) else {}
    except ValueError:
        try:
            parsed = ast.literal_eval(raw)
            return parsed if isinstance(parsed, dict) else {}
        except Exception:
            return {}


def _file_payload_from_path(path_value: object) -> dict | None:
    if not isinstance(path_value, str) or not path_value.strip():
        return None

    file_path = Path(path_value.strip())
    if not file_path.exists() or not file_path.is_file():
        return None

    content = file_path.read_bytes()
    mime_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"

    return {
        "filename": file_path.name,
        "mime_type": mime_type,
        "content_base64": base64.b64encode(content).decode("ascii"),
    }


def _collect_generated_files(result: object) -> list[dict]:
    if not isinstance(result, dict):
        return []

    candidates: list[object] = []

    messages = result.get("messages")
    saw_export_success_message = False
    if isinstance(messages, list):
        last_human_index = -1
        for i, msg in enumerate(messages):
            if isinstance(msg, HumanMessage):
                last_human_index = i

        current_turn_messages = (
            messages[last_human_index + 1 :] if last_human_index >= 0 else messages
        )

        for msg in current_turn_messages:
            if isinstance(msg, ToolMessage):
                parsed = _parse_content(getattr(msg, "content", None))
                for key in ("file_path", "filePath", "path"):
                    if key in parsed:
                        candidates.append(parsed.get(key))
                continue

            if isinstance(msg, AIMessage):
                text = _message_to_text(getattr(msg, "content", None)) or ""
                if "excel export created" in text.lower():
                    saw_export_success_message = True
                for match in re.finditer(r"'([^']+\.[A-Za-z0-9]+)'", text):
                    candidates.append(match.group(1))

    if not candidates and saw_export_success_message:
        exported_file_path = result.get("exported_file_path")
        if isinstance(exported_file_path, str) and exported_file_path.strip():
            candidates.append(exported_file_path)

    files: list[dict] = []
    seen_paths: set[str] = set()

    for candidate in candidates:
        if not isinstance(candidate, str):
            continue
        key = candidate.strip()
        if not key or key in seen_paths:
            continue

        file_payload = _file_payload_from_path(candidate)
        if file_payload is None:
            continue

        seen_paths.add(key)
        files.append(file_payload)

    return files


def _message_to_text(content: object) -> str | None:
    if isinstance(content, str):
        value = content.strip()
        return value or None

    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                value = item.strip()
                if value:
                    parts.append(value)
            elif isinstance(item, dict):
                text_value = item.get("text")
                if isinstance(text_value, str) and text_value.strip():
                    parts.append(text_value.strip())
        if parts:
            return "\n".join(parts)

    return None


def _last_ai_text(messages: object) -> str:
    if not isinstance(messages, list):
        return ""

    for msg in reversed(messages):
        if not isinstance(msg, AIMessage):
            continue

        text = _message_to_text(getattr(msg, "content", None))
        if text:
            return text

    return ""


@app.post("/chat")
async def chat(req: ChatRequest):
    config = {"configurable": {"thread_id": req.thread_id}}
    result = await graph.ainvoke(
        {"messages": [HumanMessage(content=req.message)]},
        config=config,
    )

    text = _last_ai_text(result.get("messages") if isinstance(result, dict) else None)
    files = _collect_generated_files(result)
    return {"response": text, "files": files}
