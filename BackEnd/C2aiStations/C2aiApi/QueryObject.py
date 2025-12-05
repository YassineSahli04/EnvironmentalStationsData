class QueryObject:
    refId = "A"
    FORMAT = "table"
    def __init__(self, sourceDataId, sqlQuery, format = FORMAT):
        self.sourceDataId = sourceDataId
        self.sqlQuery = sqlQuery
        self.format = format

    def getQuery(self):
        return {
            "refId": self.refId,
            "datasourceId": self.sourceDataId,
            "rawSql": self.sqlQuery,
            "format": self.format,
        }