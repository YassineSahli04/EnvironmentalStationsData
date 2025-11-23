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

    def __init__(
        self,
        station_id: str,
        name: str | None = None,
        location: str | None = None,
        manufacturer: str | None = None,
        type: str | None = None,
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
        self.Type = type
        self.Latitude = latitude
        self.Longitude = longitude
        self.Altitude = altitude
        self.DataSourceId = data_source_id
        self.DataTableName = data_table_name

    def set_or_update_station_data(self, engine:_engine.Engine):
        query = text(f"SELECT * FROM \"Stations\" Where \"Id\"= :id;")

        with engine.connect() as connection:
            result = connection.execute(query, {"id": self.Id})
            row = result.mappings().first()

        if not row:
            return

        self.Name          = row.get("Name")
        self.Location      = row.get("Location")
        self.Manufacturer  = row.get("Manufacturer")
        self.Type          = row.get("Type")
        self.Latitude      = row.get("Latitude")
        self.Longitude     = row.get("Longitude")
        self.Altitude      = row.get("Altitude")
        self.DataSourceId  = row.get("DataSourceId")
        self.DataTableName = row.get("DataTableName")

    

    