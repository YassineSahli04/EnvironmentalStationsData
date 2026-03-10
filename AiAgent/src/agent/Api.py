from fastapi import FastAPI
from pydantic import BaseModel
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from pathlib import Path
import base64
import mimetypes
from agent.Agent import Agent
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

@app.post("/chat")
async def chat(req: ChatRequest):
    config = {"configurable": {"thread_id": req.thread_id}}
    result = await graph.ainvoke(
        {"messages": [HumanMessage(content=req.message)]},
        config=config,
    )

    ai_response, ai_text =  Agent.last_ai_text(result.get("messages"))

    gen_file = _collect_generated_file(ai_response)
    return {"response": ai_text, "files": gen_file}

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
    print(file_path.name, flush=True)

    return {
        "filename": file_path.name,
        "mime_type": mime_type,
        "content_base64": base64.b64encode(content).decode("ascii"),
    }
