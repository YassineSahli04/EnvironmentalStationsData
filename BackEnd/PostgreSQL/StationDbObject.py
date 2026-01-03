import sqlalchemy.engine as _engine
from sqlalchemy import text
from datetime import datetime, timezone
from enum import Enum
from BackEnd.PostgreSQL.SensorDbObject import SensorDbObject
from dataclasses import dataclass


class StationDataGroup(Enum):
    hourly= 'hour'
    daily =  'day'
    monthly = 'month'

@dataclass
class StationSerializable:
    Id: str
    Name: str | None
    Location: str | None
    Manufacturer: str | None
    Type: str | None
    Latitude: float | None
    Longitude: float | None
    Altitude: float | None
    LastDataPointTime: datetime | None

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
    HasDataTable: bool
    LastDataPointTime: datetime | None

    def __init__(
        self,
        engine:_engine.Engine,
        station_id: str
    ):
        self.Id = station_id
        self.engine = engine
        self.set_station_metadata()

    def set_station_metadata(self):
        query = text(f"SELECT * FROM \"Stations\" Where \"Id\"= :id;")

        with self.engine.connect() as connection:
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
        self.set_has_data_table()
        self.set_last_data_point_time()

    def set_has_data_table(self):
        query = text("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = :dataTableName);")
        with self.engine.connect() as connection:
            result = connection.execute(query, {"dataTableName":self.Id}).fetchone()
        self.HasDataTable = result[0] # type: ignore
    

    def set_last_data_point_time(self):
        if self.Manufacturer is None or not self.HasDataTable: self.LastDataPointTime = None; return;
    
        allowed = {"DeltaOHM", "Pessl"}
        if self.Manufacturer not in allowed:
            raise Exception("Data Tables are only available for DeltaOHM Stations and Pessl")
        
        with self.engine.connect() as connection:
            lastDateTimeQuery = text(f"SELECT MAX(\"date_time\" AT TIME ZONE 'UTC') FROM \"{self.Id}\";")
            time = connection.execute(lastDateTimeQuery).scalar()
            if(time is not None):
                utcTime = time.replace(tzinfo=timezone.utc)
                self.LastDataPointTime = utcTime
                return
            self.LastDataPointTime = None

    def getSensorData(self, sensorId:str, dataGroup:str, startDtUTC :datetime, endDtUTC:datetime):
        try:
            dataGroup = StationDataGroup(dataGroup).value # type: ignore 
        except Exception as e:
            allowed = [e.value for e in StationDataGroup]
            raise ValueError(f"Invalid dataGroup '{dataGroup}'. Allowed: {allowed}")

        sensor = SensorDbObject(self, sensorId, isDataInDf=False)
        sensor.setSensorData(dataGroup, startDtUTC, endDtUTC)
        return sensor.getSerializableObj()
        

    def getSerializableObj(self) -> StationSerializable:
        return StationSerializable(
            Id = self.Id,
            Name = self.Name,
            Location = self.Location,
            Manufacturer = self.Manufacturer,
            Type = self.Type,
            Latitude = self.Latitude,
            Longitude = self.Longitude,
            Altitude = self.Altitude,
            LastDataPointTime = self.LastDataPointTime
        )
    

    