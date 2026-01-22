from SemanticSearch.ColumnSemanticSearch import ColumnSemanticSearch
from Worker.PostgreSQL import PostgreSQL

_semantic = None
_postgres = None

def get_semantic():
    global _semantic
    if _semantic is None:
        _semantic = ColumnSemanticSearch()
    return _semantic

def get_postgres():
    global _postgres
    if _postgres is None:
        _postgres = PostgreSQL()
    return _postgres

def setColumParam(stationId, columnName, sensorData):
    semantic = get_semantic()
    postgres = get_postgres()
    param, score = semantic.getPredictedParam(sensorData)
    postgres.updateParamInStationColumnTable(stationId, columnName, param, score) # type: ignore
