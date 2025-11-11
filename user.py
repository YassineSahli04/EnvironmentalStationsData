from API_call import api_call

def get_user_info():
    endpoint = '/user'
    method = 'GET'
    return api_call(method, endpoint)

def get_all_stations():
    endpoint='/user/stations'
    method='GET'
    return api_call(method, endpoint)