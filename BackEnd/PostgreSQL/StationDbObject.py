import sqlalchemy.engine as _engine
from sqlalchemy import text
from datetime import datetime, timezone, timedelta
from enum import Enum
from BackEnd.PostgreSQL.SensorDbObject import SensorDbObject, SensorSerializable
from dataclasses import dataclass
from BackEnd.Utils.TransformData import TransformData


class StationDataGroup(Enum):
    hourly= 'hour'
    daily =  'day'
    weekly= 'week'
    monthly = 'month'

    @classmethod
    def parse(cls, raw: object) -> str:
        if isinstance(raw, cls):
            return raw.value
        if isinstance(raw, str):
            s = raw.strip().lower()

            if s in cls.__members__:
                return cls.__members__[s].value

            for e in cls:
                if e.value == s:
                    return e.value
            
        allowed_names = list(cls.__members__.keys())
        allowed_values = [e.value for e in cls]
        raise ValueError(
            f"Invalid dataGroup {raw!r}. "
            f"Allowed names: {allowed_names}. Allowed values: {allowed_values}."
        )

class StationState(Enum):
    Online= 'Online'
    Offline= 'Offline'
@dataclass
class StationSerializable:
    Id: int
    Name: str | None
    Location: str | None
    Manufacturer: str | None
    Type: str | None
    Latitude: float | None
    Longitude: float | None
    Altitude: float | None
    SensorsList: list[SensorSerializable] | None
    LastDataPointTime: datetime | None
    State: str | None

class StationDbObject:
    Id: int
    HardwareStationIds: list[str] | None
    Name: str | None
    Location: str | None
    Manufacturer: str | None
    Type: str | None
    Latitude: float | None
    Longitude: float | None
    Altitude: float | None
    LastDataPointTime: datetime | None
    Sensors: dict[str, SensorDbObject] | None
    serializedSensors: list[SensorSerializable] | None

    DataSourceId: int | None
    HasDataTable: bool | None
    LastDataPointTime: datetime | None
    State: StationState | None
    HasStateChanged: bool | None

    def __init__(
        self,
        engine:_engine.Engine,
        id: int,
        isHardwareId: bool = False
    ):
        self.Id = id
        self.IsHardwareId = isHardwareId
        self.engine = engine
        self.set_station_metadata()

    def set_station_metadata(self):
        match self.IsHardwareId:
            case True:
                query = text(f"SELECT * FROM \"Stations\" Where \"HardwareId\"= :id;")
            case False:
                query = text(f"SELECT * FROM \"Stations\" Where \"StationId\"= :id;")

        with self.engine.connect() as connection:
            result = connection.execute(query, {"id": self.Id})
            rows = result.mappings().all()

        if not rows:
            return
        
        self.Name = None
        self.Location = None
        self.Manufacturer = None
        self.Type = None
        self.Latitude = None
        self.Longitude = None
        self.Altitude = None
        self.DataSourceId = None
        self.State = None
        self.HardwareStationIds = []
        
        for row in rows:
            self.HardwareStationIds.append(row.get("HardwareId")) # type: ignore
            
            self.Name          = row.get("Name")

            self.Location      = row.get("Location")

            self.Manufacturer  = row.get("Manufacturer")
            
            rowType          = row.get("Type")
            if self.Type is None:
                self.Type = rowType
            else:
                self.Type += f" / {rowType}"

            self.Latitude      = row.get("Latitude")
            self.Longitude     = row.get("Longitude")

            rowAltitude      = row.get("Altitude")
            if self.Altitude is None:
                self.Altitude = rowAltitude
            else:
                self.Altitude = (self.Altitude + rowAltitude) / 2 # type: ignore
            
            self.DataSourceId  = row.get("DataSourceId")

            rowState = StationState(row.get("State"))  # type: ignore            
            if self.State is None:
                self.State = rowState
            else:
                if self.State != rowState:
                    if self.State == StationState.Offline or rowState == StationState.Offline:
                        self.State = StationState.Offline
                    else:
                        self.State = StationState.Online
        self.set_has_data_table()
        self.set_last_data_point_time()
        self.setAvailableSensors()

    def set_has_data_table(self):
        ids = self.HardwareStationIds or []
        if not ids:
            self.HasDataTable = False
            return

        query = text("""
            SELECT EXISTS (
            SELECT 1
            FROM information_schema.tables
            WHERE table_schema = 'public'
                AND table_name = :name
            );
        """)

        with self.engine.connect() as conn:
            self.HasDataTable = all(
                conn.execute(query, {"name": hrd_id}).scalar()
                for hrd_id in ids
            )

    def set_last_data_point_time(self):
        if self.Manufacturer is None or not self.HasDataTable: self.LastDataPointTime = None; return;
    
        allowed = {"DeltaOHM", "Pessl"}
        if self.Manufacturer not in allowed:
            raise Exception("Data Tables are only available for DeltaOHM Stations and Pessl")
        
        self.LastDataPointTime = None
        with self.engine.connect() as connection:
            for hrdId in self.HardwareStationIds: # type: ignore
                lastDateTimeQuery = text(f"SELECT MAX(\"date_time\" AT TIME ZONE 'UTC') FROM \"{hrdId}\";")
                time = connection.execute(lastDateTimeQuery).scalar()
                if(time is not None):
                    utcTime = time.replace(tzinfo=timezone.utc)
                    if self.LastDataPointTime is None:
                        self.LastDataPointTime = utcTime
                    else:
                        if utcTime < self.LastDataPointTime:
                            self.LastDataPointTime = utcTime
  
    def updateStationState(self):
        state = StationState.Offline
        if self.LastDataPointTime is not None:
            current_utc = datetime.now(timezone.utc)
            seconds_diff = (current_utc - self.LastDataPointTime).total_seconds()
            
            if seconds_diff < 7200:
                state = StationState.Online
        self.State = state

        stateCheckQuery = text("SELECT \"State\" FROM \"Stations\" WHERE \"StationId\" = :station_id;")
        with self.engine.begin() as connection:
            res = connection.execute(stateCheckQuery, {"station_id": self.Id}).fetchone()
            if res is None:
                self.HasStateChanged = None
                return
            oldState = res[0]
        if oldState == state.value:
            self.HasStateChanged = False
            return
        self.HasStateChanged = True   

    def setAvailableSensors(self):
        if not self.HasDataTable: self.Sensors = None; self.serializedSensors = None; return;
        
        self.Sensors = {}
        self.serializedSensors = []
        query = text("""
            SELECT "param"
            FROM "StationColumn"
            WHERE "station_id" = :stationId
        """)
        with self.engine.begin() as connection:
            res = connection.execute(query, {"stationId": self.Id}).fetchall()
        sensorsList = set([elem[0] for elem in res])
        for sensor in sensorsList:
            sensorObj = SensorDbObject(self, sensor, isDataInDf=False)
            self.Sensors[sensor] = sensorObj
            serializedSensor = sensorObj.getSerializableObj(data=None)
            self.serializedSensors.append(serializedSensor)
    
    def getSensorAllDataColumns(self, sensorId:str, dataGroup:str, startDtUTC :datetime, endDtUTC:datetime):
        dataGroup = StationDataGroup.parse(dataGroup)
        sensor = SensorDbObject(self, sensorId, isDataInDf=False)
        data = sensor.getSensorAllDataColumns(dataGroup, startDtUTC, endDtUTC)
        if type(data) != list:
            return
        return sensor.getSerializableObj(data)
    
    def getSensonsDefaultDataColumns(self, sensorIdsList:list[str], dataGroup:str, startDtUTC :datetime, endDtUTC:datetime):
        dataGroup = StationDataGroup.parse(dataGroup)

        parts: dict[str, list[str]] = {}
        for sensorId in sensorIdsList:
            sensor = SensorDbObject(self, sensorId, isDataInDf=False)
            key, col = sensor.getDefaultSensorColumn()
            expr = f'{key}("{col}") AS "{sensorId}"'
            parts.setdefault(sensor.tableName, []).append(expr)

        dfs = []
        for tableName, exprs in parts.items():
            aggSelectDefaultSensorCol = ",\n".join(exprs)
            df = SensorDbObject.getdfFromQueryResult(self.engine, tableName, aggSelectDefaultSensorCol, dataGroup, startDtUTC, endDtUTC)
            dfs.append(df)

        finalDf = TransformData.combine_dfs_with_diff_timestamp(dfs, "Date/Time")      
        data = SensorDbObject.dfToTimeValueRecords(finalDf, sensorIdsList, startDtUTC)
        return data
    
    def updateStateInfo(self, station: StationSerializable):
        query = text("""
            UPDATE "Stations"
            SET 
                "Name" = :newName,
                "Location" = :newLocation,
                "Latitude" = :newLatitude,
                "Longitude" = :newLongitude,
                "Altitude" = :newAltitude
            WHERE
                "HardwareId" = :hardwareId
        """)
        with self.engine.begin() as connection:
            for hardwareId in self.HardwareStationIds: # type: ignore
                connection.execute(query, {
                    "newName": station.Name,
                    "newLocation": station.Location,
                    "newLatitude": station.Latitude,
                    "newLongitude": station.Longitude,
                    "newAltitude": station.Altitude,
                    "hardwareId": hardwareId
                })
        self.set_station_metadata()



    
    def addVpdColOrUpdate(self):
        if self.Sensors is None: 
            return
        if self.Type in ('Aquachek', 'Drill and Drop'):
            return
        
        sensors = self.Sensors
        updateVpd = False
        if 'vpd' in sensors:
            updateVpd = True 

        temp = sensors.get('temperature')
        rh   = sensors.get('relative humidity')
        
        if not temp or not rh:
            return

        if temp.tableName != rh.tableName:
            return
        
        if (not updateVpd):
            with self.engine.begin() as connection:
                connection.execute(
                    text(f'ALTER TABLE "{temp.tableName}" ADD COLUMN IF NOT EXISTS "vpd" DOUBLE PRECISION;')
                )
                insertVpd = text("""
                    INSERT INTO "StationColumn"
                    ("table_name", "station_id","column_name","data_type","unit","aggregation","param","confidence","source")
                    VALUES
                    (:tableName, :stationId, 'vpd', 'NUMERIC(10,3)', 'kPa', ARRAY['avg'], 'vpd', NULL, 'manual')

                """)
                connection.execute(insertVpd, {'tableName':temp.tableName, 'stationId': self.Id})
        self.insertVpdData(temp.tableName, updateVpd)

    def insertVpdData(self, tableName: str, isUpdate: bool):
        startDt = datetime.min.replace(tzinfo=timezone.utc)
        vpdSensorObj = SensorDbObject(self, 'vpd', isDataInDf=False)
        if isUpdate:
            lastSensorDt, lastSensorData = vpdSensorObj.getLastSensorData()
            if lastSensorDt is not None:
                startDt = lastSensorDt + timedelta(minutes=1)
        with self.engine.begin() as connection:
            temp_col = self.Sensors["temperature"].columnNames["avg"] # type: ignore
            rh_col   = self.Sensors["relative humidity"].columnNames["avg"] # type: ignore

            t  = f'"{temp_col}"'
            rh = f'"{rh_col}"'

            raw_expr = (
                f'(1.0 - ({rh} / 100.0)) * 0.6108 * '
                f'EXP((17.27 * {t}) / ({t} + 237.3))'
            )
            expr = f'ROUND(({raw_expr})::numeric, 2)'

            connection.execute(
                text(f"""
                    UPDATE "{tableName}" AS t
                    SET "{vpdSensorObj.columnNames['avg']}" = v.calc
                    FROM (
                        SELECT
                            "date_time",
                            ({expr}) AS calc
                        FROM "{tableName}"
                        WHERE "date_time" >= :start_dt
                    ) AS v
                    WHERE t."date_time" = v."date_time"
                    AND v.calc IS NOT NULL
                    AND t."{vpdSensorObj.columnNames['avg']}" IS NULL;
                """),
                {"start_dt": startDt},
            )   

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
            LastDataPointTime = self.LastDataPointTime,
            SensorsList=self.serializedSensors,
            State = self.State.value # type: ignore
        )
    