from dataclasses import dataclass
from datetime import datetime
import sqlalchemy.engine as _engine
from sqlalchemy import text
from enum import Enum

class UserRole(Enum):
    User = 'user'
    Admin = 'admin'
    Guest = 'guest'

@dataclass
class UserSerializable:
    Id: str
    FirstName: str
    LastName: str
    Email: str
    Role: str
    CreatedAt: datetime
    IsSubscribedToStationAlerts: bool
    TypeFilter: list[str]

class User:
    Id: str
    ClerkId: str
    FirstName: str
    LastName: str
    Email: str
    Role: UserRole
    CreatedAt: datetime
    IsSubscribedToStationAlerts: bool
    TypeFilter: list[str]

    def __init__(
        self,
        engine:_engine.Engine
    ):
        self.engine = engine

    @classmethod
    def from_id(cls, engine: _engine.Engine, id: str):
        user = cls(engine)
        user._fetch_by_column("id", id)
        return user

    @classmethod
    def from_clerk_id(cls, engine: _engine.Engine, clerk_id: str):
        user = cls(engine)
        user._fetch_by_column("clerk_user_id", clerk_id)
        return user

    def _fetch_by_column(self, column: str, value: str):
        query = text(f'SELECT * FROM "Users" WHERE "{column}" = :value')
        
        with self.engine.connect() as connection:
            result = connection.execute(query, {"value": value})
            row = result.mappings().first()
        
        if not row:
            return

        self.Id = row.get("id") # type: ignore
        self.ClerkId = row.get("clerk_user_id") # type: ignore
        self.FirstName = row.get("first_name") # type: ignore
        self.LastName = row.get("last_name") # type: ignore
        self.Email = row.get("email") # type: ignore
        self.Role = UserRole(row.get("role")) # type: ignore
        self.CreatedAt = row.get("created_at") # type: ignore
        self.IsSubscribedToStationAlerts  = row.get("issubscribedtostationalerts") # type: ignore
        self.TypeFilter = row.get("type_filter") # type: ignore

    
    def updateUser(self, newSubscription: bool | None = None, newRole: str | None = None):
        updates = []
        params = {"id": self.Id}
        
        if newSubscription is not None and newSubscription != self.IsSubscribedToStationAlerts:
            updates.append('"issubscribedtostationalerts" = :subscription')
            params["subscription"] = newSubscription # type: ignore
        
        if newRole is not None and newRole != self.Role.value:
            updates.append('"role" = :role')
            params["role"] = newRole
        
        if not updates:
            return
        
        query = text(f'UPDATE "Users" SET {", ".join(updates)} WHERE "id" = :id')
        
        with self.engine.begin() as connection:
            connection.execute(query, params)
        
        if newSubscription is not None:
            self.IsSubscribedToStationAlerts = newSubscription
        if newRole is not None:
            self.Role = UserRole(newRole)
        
    @classmethod
    def getGuestUser(cls, engine: _engine.Engine) -> "User":
        guest = cls(engine)
        guest.ClerkId = 'guestClerkId'
        guest.Email = 'guest@gmail.com'
        guest.Role = UserRole.Guest
        guest.TypeFilter = [
            "Pyranometer",
            "Pluviometer",
            "Meteorological",
            "Meteorological/Pluviometer",
        ] 
        return guest

    
    def getSerializableUser(self):
        return UserSerializable(
            Id=self.Id,
            FirstName=self.FirstName,
            LastName=self.LastName,
            Email=self.Email,
            Role=self.Role.value,
            CreatedAt=self.CreatedAt,
            IsSubscribedToStationAlerts=self.IsSubscribedToStationAlerts,
            TypeFilter=self.TypeFilter
        )