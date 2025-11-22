import sqlalchemy.engine as _engine
from sqlalchemy import text

class StationDbObject:
    Id: str
    Name: str | None
    Location: str | None
    Manufacturer: str | None
    Type: str | None
    Latitude: float | None
    Longitude: float | None
    Altitude: float | None
    DataSourceId: int | None
    DataTableName: str | None

    engine: _engine.Engine;

    def __init__(
        self,
        engine: _engine.Engine,
        station_id: str,
        name: str | None = None,
        location: str | None = None,
        manufacturer: str | None = None,
        type_: str | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
        altitude: float | None = None,
        data_source_id: int | None = None,
        data_table_name: str | None = None,
    ):
        self.Id = station_id
        self.Name = name
        self.Location = location
        self.Manufacturer = manufacturer
        self.Type = type_
        self.Latitude = latitude
        self.Longitude = longitude
        self.Altitude = altitude
        self.DataSourceId = data_source_id
        self.DataTableName = data_table_name

        self.engine = engine

    def set_or_update_station_data(self):
        query = text(f"SELECT * FROM \"Stations\" Where \"Id\"= :id;")

        with self.engine.connect() as connection:
            result =connection.execute(query, {"id": self.Id})  
            row = result.fetchone()
            if not row:
                return
        row = row._to_tuple_instance()

        self.Name = row[1]
        self.Location = row[2]
        self.Manufacturer = row[3]
        self.Type = row[4]
        self.Latitude = row[5]
        self.Longitude = row[6]
        self.Altitude = row[7]
        self.DataSourceId = row[8]

        self.DataTableName = row[9] if len(row) > 9 else None

