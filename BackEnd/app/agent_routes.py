from fastapi import APIRouter, HTTPException
from BackEnd.PostgreSQL.StationDbObject import StationDbObject
import logging
import traceback
from BackEnd.app.db import db
import os
import httpx
import json
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/agent",
    tags=["agent"],
)

class AgentChatRequest(BaseModel):
    message: str
    user_id: str
    conv_id: str


@router.get("/stations")
def get_all_stations_for_agent():
    try:
        stations = db.get_all_station_objects()
        return [st.getSerializableObj() for st in stations]
    except ValueError as e:
        logger.warning(
            "%s", e
        )
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        tb_last = traceback.extract_tb(e.__traceback__)[-1]
        logger.error(
            "Error while getting all stations for agent route: (%s) at %s:%s in %s",
            e,
            tb_last.filename,
            tb_last.lineno,
            tb_last.name,
        )
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.get("/stations/{stationId}")
def get_station_for_agent(stationId: int):
    try:
        station = StationDbObject(db.engine, stationId)
        if not hasattr(station, "State"):
            raise ValueError("Station not found")
        return station.getSerializableObj()
    except ValueError as e:
        logger.warning(
            "%s", e
        )
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        tb_last = traceback.extract_tb(e.__traceback__)[-1]
        logger.error(
            "Error while getting station %s for agent route: (%s) at %s:%s in %s",
            stationId,
            e,
            tb_last.filename,
            tb_last.lineno,
            tb_last.name,
        )
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
@router.post("/chat")
async def chat(req: AgentChatRequest):
    thread_id = f"{req.user_id}:{req.conv_id}"
    agent_base_url = _get_agent_url()
    agent_chat_url = f"{agent_base_url}/chat"

    async with httpx.AsyncClient() as client:
        response = await client.post(
            agent_chat_url,
            json={"message": req.message, "thread_id": thread_id},
        )

    response.raise_for_status()
    try:
        return response.json()
    except ValueError:
        # Backward-compatible fallback if ai-agent still serves SSE.
        raw = response.text or ""
        delta_parts: list[str] = []
        last_assistant: str | None = None

        for line in raw.splitlines():
            if not line.startswith("data:"):
                continue

            payload = line[5:].strip()
            if not payload:
                continue

            try:
                event = json.loads(payload)
            except ValueError:
                continue

            if not isinstance(event, dict):
                continue

            evt_type = event.get("type")
            content = event.get("content")
            if not isinstance(content, str) or not content.strip():
                continue

            if evt_type == "assistant":
                last_assistant = content
            elif evt_type == "assistant_delta":
                delta_parts.append(content)

        if delta_parts:
            return {"response": "".join(delta_parts)}
        if last_assistant:
            return {"response": last_assistant}

        raise HTTPException(status_code=502, detail="Agent returned a non-JSON response.")


def _get_agent_url() -> str:
    agent_url = os.getenv("AGENT_URL")
    if not agent_url:
        raise ValueError('The Agent URL value is not defined.')
    return agent_url
