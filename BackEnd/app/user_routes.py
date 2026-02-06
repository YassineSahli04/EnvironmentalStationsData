from fastapi import APIRouter, Depends, HTTPException, Request
from clerk_backend_api import RequestState

import logging, traceback

from BackEnd.PostgreSQL.PostgreSQL import PostgreSQL
from BackEnd.PostgreSQL.User import User, UserRole
from BackEnd.app.ClerkAuthentication import ClerkAuthentication
from pydantic import BaseModel

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
def syncUser(auth: RequestState = Depends(require_auth)):
    try:
        clerk_auth.get_or_create_user(auth)
        role = clerk_auth.getClerkUserRole(auth)
        if role is None:
            return { "id": auth.payload["sub"], "role": None } # type: ignore
        return { "id": auth.payload["sub"], "role": role.value } # type: ignore
    
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

@router.get("/all")
def get_all_users(auth: RequestState = Depends(require_auth)):
    try:
        role = clerk_auth.getClerkUserRole(auth)

        if role is None or role != UserRole.Admin:
            raise HTTPException(status_code=403, detail="User is not authorized to access this resource")

        users = db.get_all_user_objects()
        usersSerializable = []
        for user in users:
            usersSerializable.append(user.getSerializableUser())
        return usersSerializable
    except ValueError as e:
        logger.warning("%s", e)
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        tb_last = traceback.extract_tb(e.__traceback__)[-1]
        logger.error("Error while getting all users: (%s) at %s:%s in %s", e, tb_last.filename, tb_last.lineno, tb_last.name)
        raise HTTPException(status_code=500, detail="Internal Server Error")
    

class UpdateUserPayload(BaseModel):
    IsSubscribedToStationAlerts: bool | None = None
    Role: str | None = None

@router.patch("/update/{userId}")
def update_user(userId: str, payload: UpdateUserPayload, auth: RequestState = Depends(require_auth)):
    try:
        role = clerk_auth.getClerkUserRole(auth)

        if role is None or role != UserRole.Admin:
            raise HTTPException(status_code=403, detail="User is not authorized to access this resource")

        user = User.from_id(db.engine, userId)

        user.updateUser(payload.IsSubscribedToStationAlerts, payload.Role)

        return User.from_id(db.engine, userId).getSerializableUser()

    except ValueError as e:
        logger.warning("%s", e)
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        tb_last = traceback.extract_tb(e.__traceback__)[-1]
        logger.error("Error while getting all users: (%s) at %s:%s in %s", e, tb_last.filename, tb_last.lineno, tb_last.name)
        raise HTTPException(status_code=500, detail="Internal Server Error")