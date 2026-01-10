from dataclasses import dataclass
from enum import Enum
import pandas as pd
import re
import sys


class CfDataType(Enum):
    Sensor=0
    Disease=1
    Calculation=2

@dataclass
class CfSensorDataInfo:
    sensor: str
    unit: str
    aggregationsType: list[str];
    dataRange: tuple

class CfSensorObject:
    sensorName: str;
    sensorId: str;
    type: CfDataType;
    decimals: int;
    unit: str;
    aggregationsType: list[str];
    data: pd.DataFrame | list;
    def __init__(self, stationDataJson, sensorId, isDataInDf = False) -> None:
        self.isDataInDf = isDataInDf
        self.sensorId = sensorId
        self.min = None
        self.max = None
        self.setDataObjectValues(stationDataJson)

    def getDataObjFromStationData(self, stationData):
        dataList = stationData.get("data") 
        for data in dataList: 
            id = data.get('name_original')
            if self.sensorId == id:
                return data
        return None
        
    def setSensorValuesRange(self):
        if len(self.aggregationsType) == 0:
            raise ValueError('No aggregations available')
        elif len(self.aggregationsType) == 1:
            data  = self.data.get(self.aggregationsType[0]) # type: ignore
            self.min, self.max = self.getMinAndMaxVals(data) # type: ignore
            return
        if 'min' in self.aggregationsType:
            data  = self.data.get('min') # type: ignore
            self.min, _max = self.getMinAndMaxVals(data) # type: ignore
        if 'max' in self.aggregationsType:
           data  = self.data.get('max') # type: ignore
           _min ,self.max = self.getMinAndMaxVals(data) # type: ignore
        if self.min is not None and self.max is not None:
            return
        if 'avg' in self.aggregationsType:
            data  = self.data.get('avg') # type: ignore
            _min, _max = self.getMinAndMaxVals(data) # type: ignore
            if self.min is None:
                self.min = _min
            if self.max is None:
                self.max = _max
        else:
            raise ValueError("The data format is not expected.")  
            
    def getMinAndMaxVals(self,valList: list):
        min = sys.maxsize
        max = -min
        for val in valList:
            if val is None:
                continue
            if val < min:
                min = val
            if val > max:
                max = val
        return min, max
 
    def getSensorDataInfo(self):
        return CfSensorDataInfo(
            sensor = self.sensorId,
            unit= self.unit,
            aggregationsType=self.aggregationsType,
            dataRange=(self.min, self.max)
        )

    def setDataObjectValues(self, stationData):
        data = self.getDataObjFromStationData(stationData) 
        if data is None:
            raise Exception(f"Sensor {self.sensorId} has No Data.")
        self.sensorName = data.get('name')
        self.type = CfDataType[data.get('type')] # type: ignore
        self.decimals = data.get('decimals')
        self.unit = data.get('unit')
        self.aggregationsType = data.get('aggr') #type: ignore
        self.data = data.get('values')
        self.setSensorValuesRange()

    @staticmethod
    def transform_data_to_df_or_csv(dataJsonObject, isColomnHeaderCombined = False) -> pd.DataFrame :
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
        
        df[("date_time", "")] = pd.to_datetime(df[("date_time", "")], utc=True, errors="coerce")

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

        
                
        


    




