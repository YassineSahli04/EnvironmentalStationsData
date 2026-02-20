from BackEnd.app.ClerkAuthentication import ClerkAuthentication
from BackEnd.app.db import db
from fastapi import Depends, HTTPException, Query, Request
from clerk_backend_api import RequestState
from BackEnd.PostgreSQL.User import UserRole

clerk_auth = ClerkAuthentication(db.engine)

def require_auth(request: Request) -> RequestState:
    request_state = clerk_auth.authenticate(request)
    if request_state is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    return request_state

def require_role(*allowed: UserRole):
    def guard(request_state: RequestState = Depends(require_auth)):
        role = clerk_auth.getClerkUser(request_state).Role
        allowedRoleValues = [role.value for role in allowed]
        if role is None or role.value not in allowedRoleValues:
            raise HTTPException(status_code=403, detail="Forbidden")
        return request_state
    return guard

def require_type_filter():
    def guard(
        request_state: RequestState = Depends(require_auth),
        typeFilter: list[str] = Query(default=[], alias="type[]"),
    ) -> None:
        user = clerk_auth.getClerkUser(request_state)
        allowed = user.TypeFilter or []
        if typeFilter is None or typeFilter == []:
            raise HTTPException(status_code=403, detail="Forbidden")

        for t in typeFilter:
            if t not in allowed:
                raise HTTPException(status_code=403, detail="Forbidden")
    return guard
