from enum import Enum
import pandas as pd

class CfDataType(Enum):
    Sensor=0
    Disease=1
    Calculation=2

class CfSensorObject:
    STATIONDATA: dict;
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
        self.STATIONDATA =  stationDataJson
        self.setDataObjectValues()

    def getDataObjFromStationData(self):
        dataList = self.STATIONDATA.get("data") 
        for data in dataList: # type: ignore
            id = data.get('name_original')
            if self.sensorId == id:
                return data
        return None
    
    def getDataValues(self, sensorFullData) -> pd.DataFrame | list:
        if self.aggregationsType is None:
           raise AttributeError('AggregationType Attribute is not defined.', self.aggregationsType)
        df = pd.DataFrame()
        df['Date/Time'] = self.STATIONDATA.get('dates')
        for aggrType in self.aggregationsType:
            values = sensorFullData.get(aggrType)
            if len(values) != len(df["Date/Time"]):
                raise ValueError(f"Aggregation '{aggrType}' length mismatch with dates.")
            df[aggrType] = values

        if(not self.isDataInDf):
            dataDf = df.copy(deep=True)
            return dataDf.to_dict(orient="records")
        return df


    def setDataObjectValues(self):
        data = self.getDataObjFromStationData() 
        if data is None:
            raise Exception(f"Sensor {self.sensorId} has No Data.")
        self.sensorName = data.get('name')
        self.type = CfDataType[data.get('type')] # type: ignore
        self.decimals = data.get('decimals')
        self.unit = data.get('unit')
        self.aggregationsType = data.get('aggr') #type: ignore
        self.data = self.getDataValues(data.get('values'))

    

    




