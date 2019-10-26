import requests
from e3372_interface import send_sms

env_agency_api_url = "https://environment.data.gov.uk/flood-monitoring/id/measures/4195-level-stage-i-15_min-mASD"
river_high = 0.8
river_high_warn = 1.1
warn_sms_recp = "+447"

resp = requests.get(env_agency_api_url)
river_level = resp.json()["items"]["latestReading"]["value"]

if river_level > river_high_warn:
    warn_sms_text = "River level at "+str(river_level)+"m!"
    send_sms(warn_sms_recp, warn_sms_text)
