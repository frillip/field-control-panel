import requests
import e3372_interface
import global_vars
from datetime import datetime

import user_data
import clickatell

import logging
import colorlog

handler = colorlog.StreamHandler()
handler.setFormatter(global_vars.log_format)
logger = colorlog.getLogger(__name__)
logger.addHandler(handler)
logger.setLevel(logging.INFO)


env_agency_api_url = "https://environment.data.gov.uk/flood-monitoring/id/measures/4195-level-stage-i-15_min-mASD"
river_warning_sent = False
river_high = 0.95
river_high_warn = 1.1

def check_river():

    global env_agency_api_url
    global river_warning_sent
    global river_high
    global river_high_warn

    try:
        resp = requests.get(env_agency_api_url)
        river_level = resp.json()["items"]["latestReading"]["value"]
        if river_level > river_high_warn and not river_warning_sent:
            logger.critical("River level at "+str(river_level)+"m! Sending alert SMS!")
            human_datetime = datetime.now().strftime("%d/%m/%Y %H:%M")
            warn_sms_text = human_datetime + ": River level at "+str(river_level)+"m!"
            if e3372_interface.net_connected():
                clickatell.send_sms(user_data.river_warn_sms_list, warn_sms_text)
            else:
                for dest in user_data.river_warn_sms_list:
                    e3372_interface.send_sms(dest, warn_sms_text)
            logger.critical("Alerts sent")
            river_warning_sent = True

        if river_warning_sent and river_level < river_high:
            logger.warning("River returned to normal levels")
            river_warning_sent = False

        pass

    except Exception as e:
        logger.error("River task failed: " + str(e))
        pass
