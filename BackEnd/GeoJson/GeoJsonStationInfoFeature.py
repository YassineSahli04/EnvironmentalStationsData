from BackEnd.GeoJson.GeoJsonFeature import GeoJsonFeature as Feature
class GeoJsonStationInfoFeature(Feature):
    def __init__(self, jsonObject: dict):
        super().__init__()
        id = jsonObject["name"]["original"]
        name = jsonObject["name"]["custom"]
        longitude = jsonObject["position"]["geo"]["coordinates"][0]
        latitude = jsonObject["position"]["geo"]["coordinates"][1]
        altitude = jsonObject["position"]["altitude"]
        self.set_data_point(latitude, longitude, altitude)
        self.add_property("id", id)
        self.add_property("name", name)
        
        
                                                