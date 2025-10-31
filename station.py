from auth import AuthHmacMetos, publicKey, privateKey, apiURI
import requests
import json

def get_station_info(stationId):
    endpoint = f'/station/{stationId}'
    method = 'GET'
    auth = AuthHmacMetos(endpoint, publicKey, privateKey, method)
    response = requests.get(apiURI+endpoint, headers={'Accept': 'application/json'}, auth=auth)
    json_object = response.json()
    json_formatted = json.dumps(json_object, indent=2)
    print(json_formatted)
    return json_object

get_station_info('031143C2')