class CfAggregationCorrector:

    @staticmethod
    def correctAggregation(param: str, agg: str):
        if param == 'solar radiation':
            return 'sum'
        return agg