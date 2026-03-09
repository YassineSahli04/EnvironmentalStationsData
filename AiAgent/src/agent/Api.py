from fastapi import FastAPI
from pydantic import BaseModel
from langchain_core.messages import AIMessage, HumanMessage
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
    return {"response": text}
