from sqlalchemy import text
import sqlalchemy.engine as _engine
import pandas as pd
from datetime import datetime, timezone, timedelta
from BackEnd.NasaStations.NasaStationsApiCalls import NasaPowerApiCalls
from BackEnd.PostgreSQL.StationColumnConverter import StationColumnConverter

class NasaTableCreator:
    def __init__(self, engine: _engine.Engine, stationId: str, lat: float, lon: float):
        self.engine = engine
        self.stationId = stationId
        self.newTableName = stationId 
        self.lat = lat
        self.lon = lon

    @staticmethod
    def get_nasa_station_id(lat: float, lon: float) -> str:
        """
        Returns a standardized ID: NASA_{lat}_{lon}
        Rounded to 2 decimals
        """
        lat_rounded = round(lat, 2)
        lon_rounded = round(lon, 2)
        return f"NASA_{lat_rounded}_{lon_rounded}"

    def create_postgre_table(self) -> bool:
        already_exists_query = text("""
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = :table_name
            );
        """)
        
        with self.engine.connect() as connection:
            exists = connection.execute(already_exists_query, {"table_name": self.newTableName}).scalar()

        if exists:
            return True

        # Create the Data Table
        create_query = text(f"""
            CREATE TABLE IF NOT EXISTS "{self.newTableName}" (
                date_time TIMESTAMPTZ PRIMARY KEY,
                T2M NUMERIC(10,3),
                T2MDEW NUMERIC(10,3),
                WS2M NUMERIC(10,3),
                RH2M NUMERIC(10,3),
                PRECTOTCORR NUMERIC(10,3),
                ALLSKY_SFC_SW_DWN NUMERIC(10,3)
            );
        """)

        with self.engine.begin() as connection:
            connection.execute(create_query)
        
        # Register the columns in StationColumn table
        self.addStationColumnsToTable()
        return False

    def addStationColumnsToTable(self):
        query = text(""" 
            INSERT INTO "StationColumn"
            ("station_id","column_name","data_type","unit","aggregation","param","confidence","source")
            VALUES
                (:station_id, 'T2M', 'NUMERIC(10,3)', '°C', ARRAY['avg','min','max']::TEXT[], 'air_temperature', NULL, 'nasa_power'),
                (:station_id, 'T2MDEW', 'NUMERIC(10,3)', '°C', ARRAY['avg','min','max']::TEXT[], 'dew_point_temperature', NULL, 'nasa_power'),
                (:station_id, 'WS2M', 'NUMERIC(10,3)', 'm/s', ARRAY['avg','min','max']::TEXT[], 'wind_speed', NULL, 'nasa_power'),
                (:station_id, 'RH2M', 'NUMERIC(10,3)', '%', ARRAY['avg','min','max']::TEXT[], 'relative_humidity', NULL, 'nasa_power'),
                (:station_id, 'PRECTOTCORR', 'NUMERIC(10,3)', 'mm', ARRAY['sum']::TEXT[], 'precipitation', NULL, 'nasa_power'),
                (:station_id, 'ALLSKY_SFC_SW_DWN', 'NUMERIC(10,3)', 'W/m²', ARRAY['avg']::TEXT[], 'solar_radiation', NULL, 'nasa_power')

            ON CONFLICT ("station_id","column_name")
            DO UPDATE SET
                "data_type"    = EXCLUDED."data_type",
                "unit"         = EXCLUDED."unit",
                "aggregation"  = EXCLUDED."aggregation",
                "param"        = EXCLUDED."param",
                "confidence"   = EXCLUDED."confidence",
                "source"       = EXCLUDED."source",
                "updated_at"   = NOW()
            WHERE
                "StationColumn"."data_type"    IS DISTINCT FROM EXCLUDED."data_type"
                OR "StationColumn"."unit"      IS DISTINCT FROM EXCLUDED."unit"
                OR "StationColumn"."aggregation" IS DISTINCT FROM EXCLUDED."aggregation"
                OR "StationColumn"."param"     IS DISTINCT FROM EXCLUDED."param";
        """)

        with self.engine.begin() as connection:
            connection.execute(query, {"station_id": self.newTableName})

    def get_last_data_point(self) -> datetime:
        query = text(f'SELECT MAX("date_time") FROM "{self.newTableName}";')
        with self.engine.connect() as conn:
            last_time = conn.execute(query).scalar()
        
        if last_time:
            if last_time.tzinfo is None:
                return last_time.replace(tzinfo=timezone.utc)
            return last_time
        
        # Default start date if table is empty (e.g. Jan 1st 2024 for MVP)
        return datetime(2024, 1, 1, tzinfo=timezone.utc)

    def update_db_table(self):
        # 1. Determine Start Date
        start_dt = self.get_last_data_point()
        end_dt = datetime.now(timezone.utc)
        
        # If we are up to date (less than 2 hours behind), skip
        if (end_dt - start_dt).total_seconds() < 7200:
            return

        # 2. Call API
        # Format dates as YYYYMMDD for NASA API (Hourly endpoint uses YYYYMMDD)
        start_str = start_dt.strftime("%Y%m%d")
        end_str = end_dt.strftime("%Y%m%d")

        api = NasaPowerApiCalls(self.lat, self.lon, start_str, end_str)
        try:
            data_json = api.get_response()
        except Exception as e:
            print(f"Failed to fetch NASA data: {e}")
            return

        # 3. Parse Response into DataFrame
        try:
            params = data_json['properties']['parameter']
            
            # Extract independent series
            # NASA returns dicts: {"2024010100": 12.3, "2024010101": 15.6...}
            t2m = pd.Series(params.get('T2M', {}), name='T2M')
            t2m_dew = pd.Series(params.get('T2MDEW', {}), name='T2MDEW')
            ws2m = pd.Series(params.get('WS2M', {}), name='WS2M')
            rh2m = pd.Series(params.get('RH2M', {}), name='RH2M')
            prec = pd.Series(params.get('PRECTOTCORR', {}), name='PRECTOTCORR')
            rad = pd.Series(params.get('ALLSKY_SFC_SW_DWN', {}), name='ALLSKY_SFC_SW_DWN')
            
            # Combine
            df = pd.concat([t2m, t2m_dew, ws2m, rh2m, prec, rad], axis=1)
            
            # Index is currently strings "YYYYMMDDHH". Convert to TIMESTAMPTZ
            df.index = pd.to_datetime(df.index, format='%Y%m%d%H', utc=True)
            df.index.name = 'date_time'
            
            # Filter to only new data (API might return overlap)
            df = df[df.index > start_dt]
            
            if df.empty:
                return

            # 4. Insert into DB
            with self.engine.begin() as connection:
                connection.execute(text("SET TIME ZONE 'UTC';"))
                df.to_sql(
                    name=self.newTableName,
                    con=connection,
                    if_exists="append",
                    index=True, # We want the date_time index
                    method="multi",
                    chunksize=1000
                )
                
        except KeyError as e:
            print(f"Error parsing NASA response: {e}")
