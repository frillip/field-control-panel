import requests
from e3372_interface import send_sms
from datetime import datetime

env_agency_api_url = "https://environment.data.gov.uk/flood-monitoring/id/measures/4195-level-stage-i-15_min-mASD"
river_warning_sent = False

def check_river():

    global env_agency_api_url
    global river_warning_sent

    river_high = 0.8
    river_high_warn = 1.1
    warn_sms_recp = "+447" # Move this elsewhere, and maybe turn it into a list?

    try:
        resp = requests.get(env_agency_api_url)
        river_level = resp.json()["items"]["latestReading"]["value"]

        if river_level > river_high_warn and not river_warning_sent:
            warn_sms_text = "River level at "+str(river_level)+"m!"
            # Don't actually do this yet
            now = datetime.now()
            timestamp = datetime.timestamp(now)
            # send_sms(warn_sms_recp, warn_sms_text)
            print("SMS send here: "+ warn_sms_text + " " + timestamp)
            river_warning_sent = True

        if river_warning_sent and river_level < river_high:
            river_warning_sent = False

        pass
    
    except:

        pass # Don't really care if this fails