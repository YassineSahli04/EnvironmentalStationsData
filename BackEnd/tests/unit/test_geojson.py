from unittest.mock import MagicMock

from BackEnd.GeoJson.GeoJsonGeometry import GeoJsonGeometry
from BackEnd.GeoJson.GeoJsonFeature import GeoJsonFeature
from BackEnd.GeoJson.GeoJsonObject import GeoJsonObject
from BackEnd.GeoJson.GeoJsonStationInfoFeature import GeoJsonStationInfoFeature


class TestGeoJsonGeometry:
    def test_to_dict(self):
        g = GeoJsonGeometry(type="Point", coordinates=[10.0, 36.8])
        d = g.to_dict()
        assert d == {"type": "Point", "coordinates": [10.0, 36.8]}

    def test_defaults(self):
        g = GeoJsonGeometry()
        d = g.to_dict()
        assert d == {"type": None, "coordinates": []}


class TestGeoJsonFeature:
    def test_full_lifecycle(self):
        f = GeoJsonFeature()
        f.add_property("name", "Station-A")
        f.set_data_point(latitude=36.8, longitude=10.1, elevation=50.0)
        d = f.to_dict()

        assert d["type"] == "Feature"
        assert d["properties"]["name"] == "Station-A"
        assert d["geometry"]["type"] == "Point"
        assert d["geometry"]["coordinates"] == [10.1, 36.8, 50.0]

    def test_set_data_point_without_elevation(self):
        f = GeoJsonFeature()
        f.set_data_point(latitude=36.8, longitude=10.1)
        assert f.geometry.coordinates == [10.1, 36.8]


class TestGeoJsonObject:
    def test_feature_collection(self):
        obj = GeoJsonObject()
        f = GeoJsonFeature()
        f.add_property("id", "1")
        obj.add_feature(f)

        d = obj.to_dict()
        assert d["type"] == "FeatureCollection"
        assert len(d["features"]) == 1
        assert d["features"][0]["properties"]["id"] == "1"

    def test_empty_collection(self):
        obj = GeoJsonObject()
        d = obj.to_dict()
        assert d == {"type": "FeatureCollection", "features": []}


class TestGeoJsonStationInfoFeature:
    def test_builds_from_station(self):
        station = MagicMock()
        station.Id = 42
        station.Name = "Tunis-Met"
        station.Manufacturer = "Pessl"
        station.Type = "Meteorological"
        station.Latitude = 36.8
        station.Longitude = 10.18
        station.Altitude = 50.0
        station.State = "Online"

        feature = GeoJsonStationInfoFeature(station)
        d = feature.to_dict()

        assert d["type"] == "Feature"
        assert d["geometry"]["coordinates"] == [10.18, 36.8, 50.0]
        assert d["properties"]["id"] == 42
        assert d["properties"]["name"] == "Tunis-Met"
        assert d["properties"]["manufacturer"] == "Pessl"
        assert d["properties"]["state"] == "Online"
