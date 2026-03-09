from fastapi import APIRouter, HTTPException
from BackEnd.PostgreSQL.StationDbObject import StationDbObject
import logging
import traceback
from BackEnd.app.db import db
import os
from fastapi.responses import StreamingResponse
import httpx

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/agent",
    tags=["agent"],
)


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
async def chat(message: str, user_id: str, conv_id: str):

    thread_id = f'{user_id}:{conv_id}'
    agent_base_url = _get_agent_url()
    agent_chat_url = f'{agent_base_url}/chat'

    async def stream():
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                agent_chat_url,
                json={"message": message, "thread_id": thread_id},             
            ) as response:
                async for chunk in response.aiter_bytes():
                    yield chunk

    return StreamingResponse(stream(), media_type="text/event-stream")


def _get_agent_url() -> str:
    agent_url = os.getenv("AGENT_URL")
    if not agent_url:
        raise ValueError('The Agent URL value is not defined.')
    return agent_url
