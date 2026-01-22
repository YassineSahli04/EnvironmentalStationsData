import json
import sqlalchemy.engine as _engine
from sqlalchemy import create_engine, text, bindparam
import os

class PostgreSQL:
    engine: _engine.Engine;
    CHUNK_SIZE = 25
    def __init__(self):
        self.SECRETJSONPATH = os.getenv("DBINFO_PATH")
        self.initialize_postgres_connection()
       
    def initialize_postgres_connection(self):
        if self.SECRETJSONPATH is None:
            raise RuntimeError("DBINFO_PATH env var is not set")
        if not os.path.exists(self.SECRETJSONPATH):
            raise RuntimeError(f"Secret file not found: {self.SECRETJSONPATH}")

        with open(self.SECRETJSONPATH, "r") as f:
            data = json.load(f)

        userName = data.get("userName")
        password = data.get("password")
        host = data.get("host")
        port = data.get("port")
        database = data.get("database")

        connection_string = f"postgresql+psycopg2://{userName}:{password}@{host}:{port}/{database}"
        self.engine = create_engine(
            connection_string,
            connect_args={"options": "-c timezone=UTC"},
        )

    def updateParamInStationColumnTable(self, stationId, columnName, param, score):
        query = text("""
            UPDATE "StationColumn"
            SET "param" = :param,
                "confidence" = :score,
                "updated_at" = NOW()
            WHERE "station_id" = :stationId
            AND "column_name" = :columnName
            AND (
                "param" IS DISTINCT FROM :param
                OR "confidence" IS DISTINCT FROM :score
            )
        """)

        with self.engine.begin() as connection:
            res = connection.execute(query, {
                "param": param,
                "score": score,
                "stationId": stationId,
                "columnName": columnName,
            })
            return res.rowcount