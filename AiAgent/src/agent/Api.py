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


@app.post("/chat")
async def chat(req: ChatRequest):

    async def event_stream():
        config = {"configurable": {"thread_id": req.thread_id}}

        async for chunk in graph.astream(
            {"messages": [HumanMessage(content = req.message)]},
            config = config
        ):
            yield f"data: {chunk}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream"
    )