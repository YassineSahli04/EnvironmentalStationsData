import os
import requests 
import traceback
import time
from datetime import datetime

URL = os.getenv("UPDATE_URL")
INTERVAL = 3600

# Ideally, store this in an environment variable, not hardcoded
WEBHOOK_URL = "https://discord.com/api/webhooks/1461909354310795490/r1fuu-7pq9wO8szKB3R_X31m5VBRryGizlLYJ1bNzlgyXRNa9DxyDv63iEkVIOB9vBrJ"

def send_discord_alert(error_message, traceback_details, error=True):
    """Sends a structured error payload to Discord."""
    payload = {
        "username": "Data Scheduler Bot",
        "embeds": [
            {
                "title": "🚨 Data Load Failure",
                "description": f"**Error:** {error_message}",
                "color": 16711680, # Red color
                "fields": [
                    {
                        "name": "Traceback",
                        "value": f"```{traceback_details[:1000]}```" # Discord limits to 1024 chars
                    }
                ],
                "footer": {
                    "text": "Server: Production-01"
                }
            }
        ]
    }
    
    try:
        response = requests.post(WEBHOOK_URL, json=payload)
        response.raise_for_status()
    except Exception as e:
        print(f"Failed to send Discord alert: {e}")


if URL is None:
    raise ValueError("The scheduler endpoint is not defined")
time.sleep(180)
while True:
    now = datetime.now()
    try:
        r = requests.post(URL)
        if r.ok:
            print(f"{now} : [scheduler] success ({r.status_code})", flush=True)
        else:
            print(f"{now} : [scheduler] failure ({r.status_code}): {r.text[:300]}", flush=True)
    except Exception as e:
        print(f"{now} : [scheduler] exception: {e}", flush=True)
        tb = traceback.format_exc()
        send_discord_alert(error_message=e,traceback_details=tb)
    time.sleep(INTERVAL)
