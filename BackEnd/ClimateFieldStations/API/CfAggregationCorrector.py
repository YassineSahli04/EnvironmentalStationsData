class CfAggregationCorrector:

    @staticmethod
    def correctAggregation(specificCol: str, agg: str):
        if "solar radiation" in specificCol.lower():
            return 'sum'
        return agg