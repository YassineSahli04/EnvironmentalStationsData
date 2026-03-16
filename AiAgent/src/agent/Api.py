from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from pathlib import Path
import base64
import mimetypes
from uuid import uuid4
from agent.Agent import Agent
from agent.Graph import build_graph
from agent.McpTools import init_tool
from agent.Logging import get_logger

app = FastAPI()
graph = build_graph()
logger = get_logger(__name__)


@app.on_event("startup")
async def startup_event():
    try:
        await init_tool()
        logger.info("startup mcp initialization succeeded")
    except Exception:
            raise ValueError("cli mcp initialization failed.")

class ChatRequest(BaseModel):
    message: str
    thread_id: str

@app.post("/chat")
async def chat(req: ChatRequest):
    config = {"configurable": {"thread_id": req.thread_id}}
    request_id = uuid4().hex[:8]

    try:
        result = await graph.ainvoke(
            {"messages": [HumanMessage(content=req.message)]},
            config=config,
        )
    except Exception:
        logger.exception(
            "chat request failed | request_id=%s thread_id=%s",
            request_id,
            req.thread_id,
        )
        return JSONResponse(
            status_code=200,
            content={
                "response": (
                    "I hit an internal error while processing your request. "
                    f"Please retry. (error_id={request_id})"
                ),
                "file": None,
            },
        )

    ai_response, ai_text =  Agent.last_ai_text(result.get("messages"))

    gen_file = _collect_generated_file(ai_response)
    logger.info(
        "chat request succeeded | request_id=%s thread_id=%s file=%s",
        request_id,
        req.thread_id,
        bool(gen_file),
    )
    return {"response": ai_text, "file": gen_file}

def _collect_generated_file(last_response: AIMessage | None):
    if not last_response:
        return None
    if "Excel export created" in last_response.content:
        file_path = last_response.additional_kwargs.get("file_path")
        if not file_path:
            return None
        return _file_payload_from_path(file_path)

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
