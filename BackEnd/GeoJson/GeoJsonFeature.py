from .GeoJsonGeometry import GeoJsonGeometry as Geometry
class GeoJsonFeature:
    geometry: Geometry
    properties: dict[str, object]

    def __init__(self):
        self.type = "Feature"
        self.geometry = Geometry()
        self.properties = {}
    
    def add_property(self, key: str, value: str):
        self.properties[key] = value

    def set_data_point(self, latitude: float, longitude: float, elevation: float | None = None):
        self.geometry.type = "Point"
        self.geometry.coordinates = [longitude, latitude, elevation] if elevation is not None else [longitude, latitude]

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "geometry": self.geometry.to_dict(),
            "properties": self.properties
        }