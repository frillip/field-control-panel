import requests
import global_vars
from datetime import datetime

import user_data
from sms_sender import send_sms
import logging
import colorlog

handler = colorlog.StreamHandler()
handler.setFormatter(global_vars.log_format)
logger = colorlog.getLogger(__name__)
logger.addHandler(handler)
logger.setLevel(logging.INFO)


env_agency_api_url = "https://environment.data.gov.uk/flood-monitoring/id/measures/4195-level-stage-i-15_min-mASD"
river_warning_sent = False
river_level_sent = 0.0
river_high = 0.95
river_high_warn = 1.1

def check_river():

    global env_agency_api_url
    global river_warning_sent
    global river_level_sent
    global river_high
    global river_high_warn

    try:
        resp = requests.get(env_agency_api_url)
        river_level = resp.json()["items"]["latestReading"]["value"]
        human_datetime = datetime.now().strftime("%d/%m/%Y %H:%M")
        if river_level > river_high_warn:
            if not river_warning_sent or ( river_warning_sent and river_level > ( river_level_sent + 0.1) ):
                if not river_warning_sent:
                    logger.critical("River level high! "+str(river_level)+"m. Sending alert SMS!")
                    warn_sms_text = human_datetime + ": River level high! "+str(river_level)+"m"
                else:
                    logger.critical("River level rising! "+str(river_level)+"m. Sending alert SMS!")
                    warn_sms_text = human_datetime + ": River level rising! "+str(river_level)+"m"
                send_sms(user_data.river_warn_sms_list, warn_sms_text)
                logger.critical("Alerts sent")
                river_level_sent = river_level
                river_warning_sent = True

        if river_warning_sent and river_level < river_high:
            logger.warning("River returned to normal levels")
            normal_sms_text = human_datetime + ": River level returned to normal. "+str(river_level)+"m"
            send_sms(user_data.river_warn_sms_list, normal_sms_text)
            river_warning_sent = False
        pass

    except Exception as e:
        logger.error("River task failed: " + str(e))
        pass
