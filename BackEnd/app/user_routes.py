from fastapi import APIRouter, Depends, HTTPException
from clerk_backend_api import RequestState
import logging, traceback
from BackEnd.PostgreSQL.User import User, UserRole
from BackEnd.app.auth import clerk_auth, require_auth, require_role
from BackEnd.app.db import db
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/users",
    tags=["users"],
)

@router.post("/sync")
def syncUser(auth: RequestState = Depends(require_auth)):
    try:
        clerk_auth.get_or_create_user(auth)
        user = clerk_auth.getClerkUser(auth)

        return { "id": user.ClerkId, "role": user.Role.value, "typeFilter":  user.TypeFilter} # type: ignore
    
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

@router.get("/all", dependencies=[Depends(require_role(UserRole.Admin))])
def get_all_users():
    try:
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

@router.patch("/update/{userId}", dependencies=[Depends(require_role(UserRole.Admin))])
def update_user(userId: str, payload: UpdateUserPayload):
    try:
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
