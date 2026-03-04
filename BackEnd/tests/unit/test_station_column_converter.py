import pytest
from unittest.mock import MagicMock, patch

from BackEnd.PostgreSQL.StationColumnConverter import (
    StationColumnConverter,
    WeatherParamDeltaohmColumns,
)


class TestWeatherParamToEnumKey:
    def test_strips_and_replaces_spaces(self):
        assert WeatherParamDeltaohmColumns.weatherParamToEnumKey("Wind Speed") == "Wind_Speed"
        assert WeatherParamDeltaohmColumns.weatherParamToEnumKey(" Temperature ") == "Temperature"

    def test_no_spaces(self):
        assert WeatherParamDeltaohmColumns.weatherParamToEnumKey("Precipitation") == "Precipitation"


@patch.object(StationColumnConverter, "getStationTableAvailableColumns", return_value=[])
class TestGetActualSensorColumnDeltaOHM:
    def test_valid_sensor(self, _mock_cols):
        conv = StationColumnConverter(
            MagicMock(), "st1", "DeltaOHM", None, "Temperature", "avg"
        )
        assert conv.getActualSensorColumn() == "air_temperature"

    def test_invalid_sensor_raises(self, _mock_cols):
        conv = StationColumnConverter(
            MagicMock(), "st1", "DeltaOHM", None, "InvalidSensor", "avg"
        )
        with pytest.raises(ValueError, match="Invalid Sensor"):
            conv.getActualSensorColumn()


class TestGetActualSensorColumnPessl:
    @patch.object(
        StationColumnConverter,
        "getStationTableAvailableColumns",
        return_value=["temperature_avg", "humidity_avg", "temperature_min"],
    )
    def test_matches_sensor_and_aggr(self, _mock_cols):
        conv = StationColumnConverter(
            MagicMock(), "st1", "Pessl", "Meteorological", "temperature", "avg"
        )
        assert conv.getActualSensorColumn() == "temperature_avg"

    @patch.object(
        StationColumnConverter,
        "getStationTableAvailableColumns",
        return_value=["temperature_avg"],
    )
    def test_single_match_fallback(self, _mock_cols):
        conv = StationColumnConverter(
            MagicMock(), "st1", "Pessl", "Meteorological", "temperature", "max"
        )
        assert conv.getActualSensorColumn() == "temperature_avg"

    @patch.object(
        StationColumnConverter,
        "getStationTableAvailableColumns",
        return_value=[],
    )
    def test_aquachek_raises(self, _mock_cols):
        conv = StationColumnConverter(
            MagicMock(), "st1", "Pessl", "Aquachek", "moisture", "avg"
        )
        with pytest.raises(NotImplementedError):
            conv.getActualSensorColumn()


@patch.object(StationColumnConverter, "getStationTableAvailableColumns", return_value=[])
class TestGetActualSensorColumnUnknown:
    def test_unknown_manufacturer_raises(self, _mock_cols):
        conv = StationColumnConverter(
            MagicMock(), "st1", "UnknownBrand", None, "temp", "avg"
        )
        with pytest.raises(Exception, match="only available for"):
            conv.getActualSensorColumn()
