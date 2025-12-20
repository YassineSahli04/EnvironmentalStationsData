from collections.abc import Iterator
import requests
import json
from BackEnd.C2aiStations.C2aiApi.QueryObject import QueryObject
import pandas as pd
import os

class C2aiStationsApiCalls:
    endPoint = None
    bearerToken = None
    listQuery : list[QueryObject]
    response : requests.Response;
    def __init__(self, listQuery:list[QueryObject]):
        self.SECRETJSONPATH = os.getenv("C2AIINFO_PATH")
        if self.SECRETJSONPATH is None:
            raise RuntimeError("C2AIINFO_PATH env var is not set")
        
        self.listQuery = listQuery
        with open(self.SECRETJSONPATH, "r") as f:
            secrets = json.load(f)
        self.endPoint = secrets.get("c2aiEndpoint", self.endPoint)
        self.bearerToken = secrets.get("bearerToken", self.bearerToken)
        self.response = requests.post(self.endPoint, headers=self.getHeaders(), json=self.getBody())
    def getBody(self):
        return {
            "queries": [query.getQuery() for query in self.listQuery]
        }

    def getHeaders(self):
        return {
            "Authorization": f"Bearer {self.bearerToken}",
            "Content-Type": "application/json"
        }
    def getRawResponse(self, isJson=False):
        if isJson:
            return json.dumps(self.response.json(), indent=2)
        return self.response.json()
    
    def getResponse(self) -> Iterator[pd.DataFrame]:
        for query in self.listQuery:
            frames = self.response.json().get("results").get(query.refId).get("frames")
            cols = []
            for frame in frames:
                fields = frame.get("schema").get("fields")
                values = frame.get("data").get("values")
                for i in range(len(fields)):
                    fieldName = fields[i].get("name")
                    fieldType = fields[i].get("type")
                    fieldValues = values[i]
                    columnName = f"{fieldName} : ({fieldType})"
                    cols.append(pd.Series(fieldValues, name=columnName))
            df = pd.concat(cols, axis=1)
            yield df




    