import sqlalchemy.engine as _engine
from sqlalchemy import text

class User:
    Name: str
    Email: str
    IsSubscribedToStationAlerts: bool
    def __init__(
        self,
        engine:_engine.Engine,
        name: str
    ):
        self.Name = name
        self.engine = engine
        self.set_user_metadata()

    def set_user_metadata(self):
        query = text(f"SELECT * FROM \"Users\" Where \"Name\"= :name;")

        with self.engine.connect() as connection:
            result = connection.execute(query, {"name": self.Name})
            row = result.mappings().first()
        if not row:
            return

        self.Name = row.get("Name") # type: ignore
        self.Email = row.get("Email") # type: ignore
        self.IsSubscribedToStationAlerts  = row.get("IsSubscribedToStationAlerts") # type: ignore