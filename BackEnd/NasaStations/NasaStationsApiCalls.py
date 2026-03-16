import requests
import json
import pandas as pd

# List of params: T2M T2MDEW WS2M RH2M ALLSKY_SFC_SW_DWN PRECTOTCORR
class NasaPowerApiCalls:
    # NASA Base Endpoint
    BASE_URL = "https://power.larc.nasa.gov/api/temporal/hourly/point"
    def __init__(self, lat, lon, start_date, end_date):
        self.lat = lat
        self.lon = lon
        self.start = start_date # Format: YYYYMMDDHH
        self.end = end_date     # Format: YYYYMMDDHH
        
    def get_params(self):
        """
        Instead of getBody(), we have get_params() to build the query string.
        """
        return {
            "parameters": "T2M,T2MDEW,WS2M,RH2M,ALLSKY_SFC_SW_DWN,PRECTOTCORR", 
            "community": "AG", 
            "longitude": self.lon,
            "latitude": self.lat,
            "start": self.start,
            "end": self.end,
            "format": "JSON"
        }
    def get_response(self):
        # The 'params' argument automatically encodes the dictionary 
        # into the URL (e.g. ?longitude=10&latitude=34...)
        response = requests.get(
            self.BASE_URL, 
            params=self.get_params(),
            timeout=10
        )
        response.raise_for_status() # Crash immediately if NASA is down (404/500)
        return response.json()

