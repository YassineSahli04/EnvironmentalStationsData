from fastapi import APIRouter, Depends, HTTPException, Request
from clerk_backend_api import RequestState

import logging, traceback

from BackEnd.PostgreSQL.PostgreSQL import PostgreSQL
from BackEnd.app.ClerkAuthentication import ClerkAuthentication

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/users",
    tags=["users"],
)

db = PostgreSQL()
clerk_auth = ClerkAuthentication(db.engine)

def require_auth(request: Request) -> RequestState:
    request_state = clerk_auth.authenticate(request)
    if request_state is None or not request_state.is_signed_in:
        raise HTTPException(status_code=401, detail="Authentication required")
    return request_state


@router.post("/sync")
def syncUser(request: Request, auth: RequestState = Depends(require_auth)):
    try:
        clerk_auth.get_or_create_user(auth)
        return {"message": "User synced successfully"}
    
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning("%s", e)
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        tb_last = traceback.extract_tb(e.__traceback__)[-1]
        logger.error(
            "Error while syncing user: (%s) at %s:%s in %s",
            e,
            tb_last.filename,
            tb_last.lineno,
            tb_last.name,
        )
        raise HTTPException(status_code=500, detail="Internal Server Error")