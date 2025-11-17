class GeoJsonGeometry:
    type: str | None
    coordinates: list[object]

    def __init__(self, type: str | None = None, coordinates: list[object] | None = None):
        self.type = type
        self.coordinates = coordinates if coordinates is not None else []

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "coordinates": self.coordinates
        }