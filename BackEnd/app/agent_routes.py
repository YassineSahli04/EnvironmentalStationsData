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
    try:
        agent_base_url = _get_agent_url()
    except ValueError as exc:
        logger.error("%s", exc)
        raise HTTPException(status_code=500, detail="Agent service is not configured.") from exc

    agent_chat_url = f"{agent_base_url}/chat"

    timeout = httpx.Timeout(connect=5.0, read=120.0, write=15.0, pool=5.0)

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                agent_chat_url,
                json={"message": req.message, "thread_id": thread_id},
            )
        response.raise_for_status()
    except httpx.ReadTimeout as exc:
        logger.warning("Agent request timed out for thread %s", thread_id)
        raise HTTPException(status_code=504, detail="Agent request timed out.") from exc
    except httpx.RequestError as exc:
        logger.error("Agent service request failed: %s", exc)
        raise HTTPException(status_code=502, detail="Agent service is unreachable.") from exc
    except httpx.HTTPStatusError as exc:
        logger.error(
            "Agent service returned HTTP %s for thread %s",
            exc.response.status_code,
            thread_id,
        )
        raise HTTPException(
            status_code=502,
            detail=f"Agent service error (status {exc.response.status_code}).",
        ) from exc

    try:
        return response.json()
    except ValueError:
        # Backward-compatible fallback if ai-agent still serves SSE.
        raw = response.text or ""
        delta_parts: list[str] = []
        last_assistant: str | None = None
        files: list[dict] = []

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

            event_files = event.get("files")
            if isinstance(event_files, list):
                for item in event_files:
                    if isinstance(item, dict):
                        files.append(item)

            event_file = event.get("file")
            if isinstance(event_file, dict):
                files.append(event_file)

            if not isinstance(content, str) or not content.strip():
                continue

            if evt_type == "assistant":
                last_assistant = content
            elif evt_type == "assistant_delta":
                delta_parts.append(content)

        if delta_parts:
            result = {"response": "".join(delta_parts)}
            if files:
                result["files"] = files
            return result
        if last_assistant:
            result = {"response": last_assistant}
            if files:
                result["files"] = files
            return result
        if files:
            return {"response": "", "files": files}

        raise HTTPException(status_code=502, detail="Agent returned a non-JSON response.")


def _get_agent_url() -> str:
    agent_url = os.getenv("AGENT_URL")
    if not agent_url:
        raise ValueError('The Agent URL value is not defined.')
    return agent_url
