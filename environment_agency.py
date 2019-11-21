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
env_agency_api_station_url = "https://environment.data.gov.uk/flood-monitoring/id/stations/4195"
river_level_previous = 0.0
river_level_sent = 0.0

def init_river():
    try:
        logger.info("Initialising river data from Environment Agency")
        resp = requests.get(env_agency_api_station_url)
        global_vars.river_data["id"] = resp.json()["items"]["stationReference"]
        global_vars.river_data["name"] = resp.json()["items"]["riverName"]
        global_vars.river_data["level"] = resp.json()["items"]["measures"]["latestReading"]["value"]
        global_vars.river_data["status"] = "steady"
        global_vars.river_data["last_reading"] = resp.json()["items"]["measures"]["latestReading"]["dateTime"][:-1]
        global_vars.river_data["last_high_level"] = 0.0
        global_vars.river_data["high"] = 0.95
        global_vars.river_data["high_warn"] = 1.1

        now_iso_stamp = datetime.now().replace(microsecond=0).isoformat()
        global_vars.river_data["last_high"] = now_iso_stamp
        global_vars.river_data["last_warn"] = now_iso_stamp

        global_vars.river_data["warning_active"] = False

        check_river()

        pass

    except Exception as e:
        logger.error("River init failed: " + str(e))
        pass


def check_river():

    global env_agency_api_url
    global river_level_previous
    global river_level_sent

    try:
        river_level_previous = global_vars.river_data["level"]
        resp = requests.get(env_agency_api_url)
        global_vars.river_data["level"] = resp.json()["items"]["latestReading"]["value"]

        if global_vars.river_data["level"] > river_level_previous:
            global_vars.river_data["status"] = "rising"
        elif global_vars.river_data["level"] < river_level_previous:
            global_vars.river_data["status"] = "falling"
        else:
            global_vars.river_data["status"] = "steady"

        global_vars.river_data["last_reading"] = resp.json()["items"]["latestReading"]["dateTime"][:-1]

        human_datetime = datetime.now().strftime("%d/%m/%Y %H:%M")
        now_iso_stamp = datetime.now().replace(microsecond=0).isoformat()
        if global_vars.river_data["level"] > global_vars.river_data["last_high_level"]:
            global_vars.river_data["last_high_level"] = global_vars.river_data["level"]
            global_vars.river_data["last_high"] = now_iso_stamp

        if global_vars.river_data["level"] > global_vars.river_data["high_warn"]:
            if not global_vars.river_data["warning_active"] or ( global_vars.river_data["warning_active"] and global_vars.river_data["level"] > ( river_level_sent + 0.1) ):
                if not global_vars.river_data["warning_active"]:
                    logger.critical("River level high! "+str(global_vars.river_data["level"])+"m. Sending alert SMS!")
                    warn_sms_text = human_datetime + ": River level high! "+str(global_vars.river_data["level"])+"m"
                else:
                    logger.critical("River level rising! "+str(global_vars.river_data["level"])+"m. Sending alert SMS!")
                    warn_sms_text = human_datetime + ": River level rising! "+str(global_vars.river_data["level"])+"m"
                send_sms(user_data.river_warn_sms_list, warn_sms_text)
                logger.critical("Alerts sent")
                river_level_sent = global_vars.river_data["level"]
                global_vars.river_data["last_high_level"] = global_vars.river_data["level"]
                global_vars.river_data["warning_active"] = True
                global_vars.river_data["last_warn"] = now_iso_stamp

        if global_vars.river_data["warning_active"] and global_vars.river_data["level"] < global_vars.river_data["high"]:
            logger.warning("River returned to normal levels")
            normal_sms_text = human_datetime + ": River level returned to normal. "+str(global_vars.river_data["level"])+"m"
            send_sms(user_data.river_warn_sms_list, normal_sms_text)
            global_vars.river_data["warning_active"] = False
        pass

    except Exception as e:
        logger.error("River task failed: " + str(e))
        pass
