from BackEnd.GeoJson.GeoJsonFeature import GeoJsonFeature as Feature
from BackEnd.PostgreSQL.StationDbObject import StationDbObject
class GeoJsonStationInfoFeature(Feature):
    def __init__(self, station:StationDbObject):
        super().__init__()
        self.set_data_point(station.Latitude, station.Longitude, station.Altitude)  # type: ignore
        self.add_property("id", station.Id)
        self.add_property("name", station.Name) # type: ignore
        self.add_property("manufacturer", station.Manufacturer) # type: ignore
        self.add_property("type", station.Type) # type: ignore
        self.add_property("state", station.State) # type: ignore
        
        
                                                