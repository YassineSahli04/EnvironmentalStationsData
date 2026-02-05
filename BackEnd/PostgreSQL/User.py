from dataclasses import dataclass
from datetime import datetime
import sqlalchemy.engine as _engine
from sqlalchemy import text
from enum import Enum

class UserRole(Enum):
    User = 'user'
    Admin = 'admin'

@dataclass
class UserSerializable:
    FirstName: str
    LastName: str
    Email: str
    Role: str
    CreatedAt: datetime
    IsSubscribedToStationAlerts: bool

class User:
    Id: str
    ClerkId: str
    FirstName: str
    LastName: str
    Email: str
    Role: str
    CreatedAt: datetime
    IsSubscribedToStationAlerts: bool

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
        self.IsSubscribedToStationAlerts  = row.get("isSubscribedToStationAlerts") # type: ignore
    
    def getSerializableUser(self):
        return UserSerializable(
            FirstName=self.FirstName,
            LastName=self.LastName,
            Email=self.Email,
            Role=self.Role.value,
            CreatedAt=self.CreatedAt,
            IsSubscribedToStationAlerts=self.IsSubscribedToStationAlerts
        )