from logging import exception
import re
import pandas as pd
from sqlalchemy import text
from BackEnd.C2aiStations.C2aiStationsApiCalls import C2aiStationsApiCalls
from BackEnd.C2aiStations.QueryObject import QueryObject 
from pathlib import Path
import sqlalchemy.engine as _engine



class TableCreator:
    CHUNK_SIZE = 5000
    SECRETJSONPATH = Path(__file__).resolve().parents[2] / "BackEnd/PostgreSQL/DbInfo.json"
    newTableName: str | None;
    mysql_ddl: str;
    sourceDataId: int;
    engine: _engine.Engine;
    def __init__(self, engine, sourceDataId, oldTableName):
        self.sourceDataId = sourceDataId
        self.oldTableName = oldTableName
        self.set_new_table_name()
        self.set_db_creation_query()
        self.engine = engine

    def set_new_table_name(self):
        query = "SELECT DATABASE();"
        queryObject = QueryObject(self.sourceDataId, query)
        apiCall = C2aiStationsApiCalls([queryObject])
        jsonResponse = apiCall.getRawResponse()
        dbName = jsonResponse.get("results").get(queryObject.refId).get('frames')[0].get('data').get('values')[0][0] # type: ignore
        self.newTableName = f"{dbName}-{self.oldTableName}"
    
    def set_db_creation_query(self):
        query = f"SHOW CREATE TABLE {self.oldTableName};"
        queryObject = QueryObject(self.sourceDataId, query)
        apiCall = C2aiStationsApiCalls([queryObject])
        jsonResponse = apiCall.getRawResponse()
        self.mysql_ddl = jsonResponse.get("results").get(queryObject.refId).get('frames')[0].get('data').get('values')[1][0] # type: ignore


    def mysql_ddl_to_postgres(self):
        ddl = self.mysql_ddl.replace("\\n", "\n")

        ddl = re.sub(r"\)\s*ENGINE=.*", ")", ddl, flags=re.IGNORECASE | re.DOTALL)

        ddl = ddl.replace("`", '"')

        if self.newTableName is not None:
            ddl = re.sub(
                r'CREATE TABLE\s+"[^"]+"',
                f'CREATE TABLE "{self.newTableName}"',
                ddl,
                count=1,
                flags=re.IGNORECASE,
            )

        ddl = re.sub(r"\bdatetime\b", "TIMESTAMP", ddl, flags=re.IGNORECASE)
        ddl = re.sub(r"\bdouble\b", "DOUBLE PRECISION", ddl, flags=re.IGNORECASE)

        ddl = re.sub(r"\bint\(\d+\)", "INTEGER", ddl, flags=re.IGNORECASE)

        ddl = re.sub(r"\bbit\(\d+\)", "BOOLEAN", ddl, flags=re.IGNORECASE)

        ddl = re.sub(r"DEFAULT b'0'", "DEFAULT FALSE", ddl, flags=re.IGNORECASE)
        ddl = re.sub(r"DEFAULT b'1'", "DEFAULT TRUE", ddl, flags=re.IGNORECASE)

        ddl = ddl.replace("DEFAULT '0000-00-00 00:00:00'", "")

        lines = ddl.splitlines()
        new_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped.upper().startswith("KEY ") and "PRIMARY KEY" not in stripped.upper():
                continue
            if stripped.upper().startswith("INDEX "):
                continue
            new_lines.append(line)

        for i in range(len(new_lines) - 1, -1, -1):
            stripped = new_lines[i].rstrip()
            if stripped.endswith(","):
                new_lines[i] = stripped[:-1]
                break
            if stripped == "" or stripped.startswith(")"):
                continue

        ddl = "\n".join(new_lines)

        ddl = ddl.strip()
        if not ddl.endswith(";"):
            ddl += ";"
        return ddl

    
    def fix_datetime(self, col: pd.Series) -> pd.Series:
        return pd.to_datetime(col, unit="ms", origin="unix", errors="coerce")
    
    def fix_boolean(self, col: pd.Series) -> pd.Series:
        return col.astype(str).map({"0": False, "1": True, "False": False, "True": True})
    
    def fix_number(self, col: pd.Series) -> pd.Series:
        return pd.to_numeric(col, errors="coerce")
    
    def transform_df(self, df: pd.DataFrame) -> pd.DataFrame:
        new_df = df.copy()

        for col in new_df.columns:
            clean_name = col.split(" : ")[0]
            
            if clean_name == "DATE_TIME":
                new_df[col] = self.fix_datetime(new_df[col])
            
            elif re.match(r"E\d{2}_\d", clean_name):
                new_df[col] = self.fix_boolean(new_df[col])
            
            elif clean_name.startswith("MEAS_"):
                new_df[col] = self.fix_number(new_df[col])
            
            elif (
                clean_name.startswith("STAT_") or
                clean_name.startswith("TYPE_") or
                clean_name.startswith("UM_")   or
                clean_name.startswith("RES_")  or
                clean_name in ("NET_ID", "ADDR_ID")
            ):
                new_df[col] = self.fix_number(new_df[col]).astype("Int64")  
        new_df.columns = [c.split(" : ")[0] for c in df.columns]   
        return new_df
    
    def insert_df(self, df):
        with self.engine.begin() as connection:
            df.to_sql(
                name=self.newTableName,
                con=connection,
                if_exists="append",
                index=False,
                method="multi",
                chunksize=self.CHUNK_SIZE
            )

    def get_filter_columns_to_keep(self) -> list[str]:
        base_columns = ["DATE_TIME", "DATE_DOUBLE", "TYPE"]
        channel_cols = [
            f"{prefix}_{i}"
            for i in range(1,13)
            for prefix in ("MEAS", "STAT", "UM", "RES")
        ]
        return base_columns + channel_cols
    
    def filter_ed_tables(self, df: pd.DataFrame) -> pd.DataFrame:
        if "ed" not in self.oldTableName:
            raise Exception("Table is not an ed_ table.")
        cols_to_keep = self.get_filter_columns_to_keep()
        return df[cols_to_keep]   
        
    def filter_postgres_columns_in_creation_query(self, ddl: str) -> str:
        if "ed" not in self.oldTableName.lower():
            return ddl

        lines = ddl.splitlines()
        
        new_lines: list[str] = []

        cols_to_keep = set(self.get_filter_columns_to_keep())

        for line in lines:
            stripped = line.strip()

            if stripped.startswith('"'):
                first_token = stripped.split()[0]
                col_name = first_token.strip('"')

                if col_name not in cols_to_keep:
                    continue

            new_lines.append(line)

        filtered_ddl = "\n".join(new_lines).strip()

        if not filtered_ddl.endswith(";"):
            filtered_ddl += ";"
        return filtered_ddl


    def create_postgre_table(self):
        postgres_ddl = self.mysql_ddl_to_postgres()
        if "ed" in self.oldTableName:
            postgres_ddl = self.filter_postgres_columns_in_creation_query(postgres_ddl)
        with self.engine.connect() as connection:
            connection.execute(text(postgres_ddl))
            connection.commit()

    def get_all_data_and_insert(self):
        query = f"SELECT * FROM {self.oldTableName};"
        queryObject = QueryObject(self.sourceDataId, query)
        apiCall = C2aiStationsApiCalls([queryObject])
        dflist = []
        for df in apiCall.getResponse():
            transformed_df = self.transform_df(df)
            if "ed" in self.oldTableName:
                transformed_df = self.filter_ed_tables(transformed_df)
            self.insert_df(transformed_df)
        
            



