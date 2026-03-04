from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

from BackEnd.PostgreSQL.StationDbObject import StationSerializable


def _serializable_station(sid=1):
    return StationSerializable(
        Id=sid,
        Name="Station-1",
        Location="Tunis",
        Manufacturer="Pessl",
        Type="Meteorological",
        Latitude=36.8,
        Longitude=10.18,
        Altitude=50.0,
        SensorsList=[],
        LastDataPointTime=None,
        State="Online",
    )


class TestGetStations:
    @patch("BackEnd.app.stations_routes.db")
    def test_200(self, mock_db, client, mock_auth_admin):
        mock_st = MagicMock()
        mock_st.getSerializableObj.return_value = _serializable_station()
        mock_db.get_all_station_objects.return_value = [mock_st]

        resp = client.get("/api/stations/all", params={"type[]": "Meteorological"})
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    @patch("BackEnd.app.stations_routes.db")
    def test_403_without_auth(self, mock_db, client, mock_auth_none):
        resp = client.get("/api/stations/all", params={"type[]": "Meteorological"})
        assert resp.status_code == 401


class TestGetStationsGeojson:
    @patch("BackEnd.app.stations_routes.db")
    def test_200(self, mock_db, client):
        mock_db.get_stations_Geojson_object.return_value = {
            "type": "FeatureCollection",
            "features": [],
        }
        resp = client.get("/api/stations/geojson")
        assert resp.status_code == 200
        assert resp.json()["type"] == "FeatureCollection"

    @patch("BackEnd.app.stations_routes.db")
    def test_404_on_value_error(self, mock_db, client):
        mock_db.get_stations_Geojson_object.side_effect = ValueError("not found")
        resp = client.get("/api/stations/geojson")
        assert resp.status_code == 404


class TestGetStationSensorsData:
    @patch("BackEnd.app.stations_routes.StationDbObject")
    def test_200(self, MockStation, client):
        instance = MagicMock()
        instance.getSensonsDefaultDataColumns.return_value = [
            {"time": "2025-01-01T00:00:00Z", "values": {"temp": 20}}
        ]
        MockStation.return_value = instance

        resp = client.get(
            "/api/stations/station/1/sensors",
            params={
                "sensorsId[]": "temperature",
                "dataGroup": "hourly",
                "startDtUTC": "2025-01-01T00:00:00",
                "endDtUTC": "2025-01-02T00:00:00",
            },
        )
        assert resp.status_code == 200

    @patch("BackEnd.app.stations_routes.StationDbObject")
    def test_500_when_sensors_undefined(self, MockStation, client):
        MockStation.side_effect = RuntimeError("boom")

        resp = client.get(
            "/api/stations/station/1/sensors",
            params={
                "sensorsId[]": "temperature",
                "dataGroup": "hourly",
                "startDtUTC": "2025-01-01T00:00:00",
                "endDtUTC": "2025-01-02T00:00:00",
            },
        )
        assert resp.status_code == 500


class TestGetStationSensor:
    @patch("BackEnd.app.stations_routes.StationDbObject")
    def test_200(self, MockStation, client):
        instance = MagicMock()
        instance.getSensorAllDataColumns.return_value = {
            "sensor": "temperature",
            "data": [],
        }
        MockStation.return_value = instance

        resp = client.get(
            "/api/stations/station/1/sensor",
            params={
                "sensorId": "temperature",
                "dataGroup": "hourly",
                "startDtUTC": "2025-01-01T00:00:00",
                "endDtUTC": "2025-01-02T00:00:00",
            },
        )
        assert resp.status_code == 200


class TestUpdateStation:
    @patch("BackEnd.app.stations_routes.StationDbObject")
    def test_200_admin(self, MockStation, client, mock_auth_admin):
        instance = MagicMock()
        instance.getSerializableObj.return_value = _serializable_station()
        MockStation.return_value = instance

        resp = client.put(
            "/api/stations/update/1",
            json={
                "Id": 1,
                "Name": "New Name",
                "Location": "Sfax",
                "Manufacturer": "Pessl",
                "Type": "Meteorological",
                "Latitude": 34.7,
                "Longitude": 10.7,
                "Altitude": 30.0,
                "SensorsList": None,
                "LastDataPointTime": None,
                "State": "Online",
            },
        )
        assert resp.status_code == 200
        instance.updateStateInfo.assert_called_once()

    @patch("BackEnd.app.stations_routes.StationDbObject")
    def test_403_without_admin(self, MockStation, client, mock_auth_none):
        resp = client.put(
            "/api/stations/update/1",
            json={
                "Id": 1,
                "Name": "X",
                "Location": None,
                "Manufacturer": None,
                "Type": None,
                "Latitude": None,
                "Longitude": None,
                "Altitude": None,
                "SensorsList": None,
                "LastDataPointTime": None,
                "State": None,
            },
        )
        assert resp.status_code == 401


class TestUpdateDb:
    @patch("BackEnd.app.stations_routes.db")
    def test_200(self, mock_db, client):
        mock_db.create_update_all_stations_data_tables.return_value = None
        resp = client.post("/api/stations/server/update-db")
        assert resp.status_code == 200
        mock_db.create_update_all_stations_data_tables.assert_called_once()
