from enum import Enum
import pandas as pd
import re

class CfDataType(Enum):
    Sensor=0
    Disease=1
    Calculation=2

class CfSensorObject:
    sensorName: str;
    sensorId: str;
    type: CfDataType;
    decimals: int;
    unit: str;
    aggregationsType: list[str];
    data: pd.DataFrame | list;
    def __init__(self, stationDataJson, sensorId, isDataInDf = True) -> None:
        self.isDataInDf = isDataInDf
        self.sensorId = sensorId
        self.setDataObjectValues(stationDataJson)

    def getDataObjFromStationData(self, stationData):
        dataList = stationData.get("data") 
        for data in dataList: # type: ignore
            id = data.get('name_original')
            if self.sensorId == id:
                return data
        return None
    
    def getDataValues(self, sensorFullData, stationData) -> pd.DataFrame | list:
        if self.aggregationsType is None:
           raise AttributeError('AggregationType Attribute is not defined.', self.aggregationsType)
        df = pd.DataFrame()
        df['Date/Time'] = stationData.get('dates')
        for aggrType in self.aggregationsType:
            values = sensorFullData.get(aggrType)
            if len(values) != len(df["Date/Time"]):
                raise ValueError(f"Aggregation '{aggrType}' length mismatch with dates.")
            df[aggrType] = values

        if(self.isDataInDf):
            return df
        
        records = []
        for _, row in df.iterrows():
            values = {aggr: row[aggr] for aggr in self.aggregationsType}
            records.append({
                "time": row["Date/Time"],
                "values": values
            })

        return records
        


    def setDataObjectValues(self, stationData):
        data = self.getDataObjFromStationData(stationData) 
        if data is None:
            raise Exception(f"Sensor {self.sensorId} has No Data.")
        self.sensorName = data.get('name')
        self.type = CfDataType[data.get('type')] # type: ignore
        self.decimals = data.get('decimals')
        self.unit = data.get('unit')
        self.aggregationsType = data.get('aggr') #type: ignore
        self.data = self.getDataValues(data.get('values'), stationData)

    @staticmethod
    def transform_data_to_df_or_csv(dataJsonObject, dataTimeZone, isColomnHeaderCombined = False, isCsv = False):
        cols = [('date_time', "")]
        sensorsData = dataJsonObject["data"]
        
        for sensorData in sensorsData:
            if sensorData['type'] != 'Sensor':
                break
            colP1 = sensorData['name']
            cols += [(colP1, v) for v in sensorData['values']]

        columns = pd.MultiIndex.from_tuples(cols, names=["sensor", "metric"])

        dataVals = []
        for i in range(len(dataJsonObject["dates"])):
            row = []
            dt = dataJsonObject["dates"][i]
            row.append(dt)
            for sensorData in sensorsData:
                if sensorData['type'] != 'Sensor':
                    break
                for valType in sensorData['values']:
                    row.append(sensorData['values'][valType][i])
            dataVals.append(row)
        df = pd.DataFrame(dataVals, columns=columns)
        
        s = pd.to_datetime(df[("date_time", "")], errors="coerce")
        s = s.dt.tz_localize(dataTimeZone)
        s = s.dt.tz_convert("UTC")
        df[("date_time", "")] = s

        df = df.dropna(subset=[("date_time", "")])
        df = df.set_index(("date_time", ""))
        df.index.name = "date_time"
        df =  df.groupby(level=0).mean(numeric_only=True)
        df = df.reset_index()

        if isColomnHeaderCombined:
            def combine_col(col_tuple):
                sensor, metric = col_tuple
                if sensor == 'date_time':
                    return sensor
                metric_str = str(metric).strip()
                return f"{sensor} - {metric_str}" if metric_str else str(sensor)
            df.columns = [combine_col(c) for c in df.columns]
        
        if isCsv: df.to_csv("test.csv", index=False); return;
        return df 

    
    @staticmethod
    def remove_duplicated_columns(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        duplicatedDfColumns = [
            col for col in df.columns
            if isinstance(col, str) and re.search(r"\s[12]\s-\s", col)
        ]

        baseCols = {}
        for vc in duplicatedDfColumns:
            base = re.sub(r"\s[12]\s-\s", " - ", vc)
            if base not in df.columns:
                df[base] = pd.NA
            baseCols.setdefault(base, set()).update([vc, base])

        for base, cols_set in baseCols.items():
            cols_list = list(cols_set)
            df[base] = df[cols_list].apply(pd.to_numeric, errors="coerce").mean(axis=1)

        return df.drop(columns=duplicatedDfColumns)

        
                
        


    




