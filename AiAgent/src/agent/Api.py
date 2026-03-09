from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage
from agent.Graph import build_graph

app = FastAPI()
graph = build_graph()

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