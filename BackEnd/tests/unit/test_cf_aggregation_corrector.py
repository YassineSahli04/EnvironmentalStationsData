from BackEnd.ClimateFieldStations.API.CfAggregationCorrector import CfAggregationCorrector


class TestCorrectAggregation:
    def test_solar_radiation_returns_sum(self):
        assert CfAggregationCorrector.correctAggregation("Solar Radiation (avg)", "avg") == "sum"
        assert CfAggregationCorrector.correctAggregation("solar radiation", "avg") == "sum"

    def test_non_solar_returns_original(self):
        assert CfAggregationCorrector.correctAggregation("Temperature", "avg") == "avg"
        assert CfAggregationCorrector.correctAggregation("Humidity", "sum") == "sum"
