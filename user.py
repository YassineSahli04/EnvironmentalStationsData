from auth import AuthHmacMetos, publicKey, privateKey, apiURI
import requests
import json

def get_user_info():
    endpoint = '/user'
    method = 'GET'
    auth = AuthHmacMetos(endpoint, publicKey, privateKey, method)
    response = requests.get(apiURI+endpoint, headers={'Accept': 'application/json'}, auth=auth)
    json_object = response.json()
    json_formatted = json.dumps(json_object, indent=2)
    print(json_formatted)