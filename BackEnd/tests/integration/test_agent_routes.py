from unittest.mock import MagicMock, patch, PropertyMock
from BackEnd.PostgreSQL.StationDbObject import StationSerializable, StationState


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


class TestGetAllStationsForAgent:
    @patch("BackEnd.app.agent_routes.db")
    def test_200(self, mock_db, client):
        mock_station = MagicMock()
        mock_station.getSerializableObj.return_value = _serializable_station()
        mock_db.get_all_station_objects.return_value = [mock_station]

        resp = client.get("/api/agent/stations")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["Name"] == "Station-1"

    @patch("BackEnd.app.agent_routes.db")
    def test_404_on_value_error(self, mock_db, client):
        mock_db.get_all_station_objects.side_effect = ValueError("no stations")

        resp = client.get("/api/agent/stations")
        assert resp.status_code == 404

    @patch("BackEnd.app.agent_routes.db")
    def test_500_on_exception(self, mock_db, client):
        mock_db.get_all_station_objects.side_effect = RuntimeError("db crash")

        resp = client.get("/api/agent/stations")
        assert resp.status_code == 500


class TestGetStationForAgent:
    @patch("BackEnd.app.agent_routes.StationDbObject")
    def test_200(self, MockStation, client):
        instance = MagicMock()
        instance.State = StationState.Online
        instance.getSerializableObj.return_value = _serializable_station(42)
        MockStation.return_value = instance

        resp = client.get("/api/agent/stations/42")
        assert resp.status_code == 200
        assert resp.json()["Id"] == 42

    @patch("BackEnd.app.agent_routes.StationDbObject")
    def test_404_when_not_found(self, MockStation, client):
        MockStation.side_effect = ValueError("Station not found")

        resp = client.get("/api/agent/stations/999")
        assert resp.status_code == 404
