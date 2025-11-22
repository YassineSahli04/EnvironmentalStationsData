from BackEnd.GeoJson.GeoJsonFeature import GeoJsonFeature

class GeoJsonObject:
    def __init__(self):
        self.type = "FeatureCollection"
        self.features: list[GeoJsonFeature] = []
    
    def add_feature(self, feature: GeoJsonFeature):
        self.features.append(feature)

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "features": [feature.to_dict() for feature in self.features]
        }