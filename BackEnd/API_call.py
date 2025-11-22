from BackEnd.auth import AuthHmacMetos, publicKey, privateKey, apiURI
import requests
import json

def api_call(method, endpoint, isJsonObject = True):
    auth = AuthHmacMetos(endpoint, publicKey, privateKey, method)
    response = requests.get(apiURI+endpoint, headers={'Accept': 'application/json'}, auth=auth)
    json_object = response.json()
    if isJsonObject: return json_object
    return json.dumps(json_object, indent=2)