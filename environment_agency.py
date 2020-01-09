import requests
from yaml_config import config
import global_vars
from datetime import datetime
from sms_sender import send_sms
import logging
import colorlog

handler = colorlog.StreamHandler()
handler.setFormatter(global_vars.log_format)
logger = colorlog.getLogger(__name__)
logger.addHandler(handler)
logger.setLevel(global_vars.log_level)

def init_river():
    try:
        logger.info("Initialising river data from Environment Agency")
        resp = requests.get(config['river']['api_station_url'])
        global_vars.river_data["id"] = resp.json()["items"]["stationReference"]
        global_vars.river_data["name"] = resp.json()["items"]["riverName"]
        global_vars.river_data["level"] = resp.json()["items"]["measures"]["latestReading"]["value"]
        global_vars.river_data["timestamp"] = resp.json()["items"]["measures"]["latestReading"]["dateTime"][:-1]
        # If this hasn't been set pull from the retrieved JSON
        if config['river']['high_warn']:
            global_vars.river_data["high_warn"] = config['river']['high_warn']
            global_vars.river_data["high"] = config['river']['high']
        else:
            global_vars.river_data["high_warn"] = resp.json()["items"]["stageScale"]["typicalRangeHigh"]
            global_vars.river_data["high"] = global_vars.river_data["high_warn"] - 0.15 # 0.15 is generally a good guess for hysteresis

        # If this hasn't been restored from save state data
        # Move to yaml_save_state in the future maybe
        now_iso_stamp = datetime.now().replace(microsecond=0).isoformat()
        if not global_vars.river_data.get("last_high"):
            global_vars.river_data["last_high"] = now_iso_stamp
        if not global_vars.river_data.get("last_high_level"):
            global_vars.river_data["last_high_level"] = 0.0
        if not global_vars.river_data.get("last_high_warn"):
            global_vars.river_data["last_high_warn"] = 0.0
        if not global_vars.river_data.get("last_level"):
            global_vars.river_data["last_level"] = now_iso_stamp
        if not global_vars.river_data.get("last_timestamp"):
            global_vars.river_data["last_timestamp"] = now_iso_stamp
        if not global_vars.river_data.get("last_warn"):
            global_vars.river_data["last_warn"] = now_iso_stamp
        if not global_vars.river_data.get("last_warn_level"):
            global_vars.river_data["last_warn_level"] = 0.0
        if not global_vars.river_data.get("warning_active"):
            global_vars.river_data["warning_active"] = False
        if not global_vars.river_data.get("status"):
            global_vars.river_data["status"] = "steady"

        check_river()

        pass

    except Exception as e:
        logger.error("River init failed: " + str(e))
        pass


def check_river():

    try:
        resp = requests.get(config['river']['api_url'])
        # If the timestamps have changed, we have a new reading, so process it
        if resp.json()["items"]["latestReading"]["dateTime"][:-1] != global_vars.river_data["timestamp"]:
            global_vars.river_data['last_timestamp'] = global_vars.river_data["timestamp"]
            global_vars.river_data["timestamp"] = resp.json()["items"]["latestReading"]["dateTime"][:-1]

            global_vars.river_data['last_level'] = global_vars.river_data["level"]
            global_vars.river_data["level"] = resp.json()["items"]["latestReading"]["value"]

            if global_vars.river_data["level"] > global_vars.river_data['last_level']:
                global_vars.river_data["status"] = "rising"
            elif global_vars.river_data["level"] < global_vars.river_data['last_level']:
                global_vars.river_data["status"] = "falling"
            else:
                global_vars.river_data["status"] = "steady"

            human_datetime = datetime.now().strftime("%d/%m/%Y %H:%M")
            now_iso_stamp = datetime.now().replace(microsecond=0).isoformat()
            if global_vars.river_data["level"] > global_vars.river_data["last_high_level"]:
                global_vars.river_data["last_high_level"] = global_vars.river_data["level"]
                global_vars.river_data["last_high"] = now_iso_stamp

            if config['river']['warn_enable']:
                if global_vars.river_data["level"] > global_vars.river_data["high_warn"]:
                    if not global_vars.river_data["warning_active"] or ( global_vars.river_data["warning_active"] and global_vars.river_data["level"] > ( global_vars.river_data['last_warn_level'] + 0.1) ):
                        if not global_vars.river_data["warning_active"]:
                            logger.critical("River level high! "+str(global_vars.river_data["level"])+"m. Sending alert SMS!")
                            warn_sms_text = human_datetime + ": River level high! "+str(global_vars.river_data["level"])+"m"
                        else:
                            logger.critical("River level rising! "+str(global_vars.river_data["level"])+"m. Sending alert SMS!")
                            warn_sms_text = human_datetime + ": River level rising! "+str(global_vars.river_data["level"])+"m"
                        send_sms(config['river']['warn_sms_list'], warn_sms_text)
                        logger.critical("Alerts sent")
                        global_vars.river_data['last_warn_level'] = global_vars.river_data["level"]
                        global_vars.river_data["last_high_level"] = global_vars.river_data["level"]
                        global_vars.river_data["warning_active"] = True
                        global_vars.river_data["last_warn"] = now_iso_stamp

                if global_vars.river_data["warning_active"] and global_vars.river_data["level"] < global_vars.river_data["high"]:
                    logger.warning("River returned to normal levels")
                    normal_sms_text = human_datetime + ": River level returned to normal. "+str(global_vars.river_data["level"])+"m"
                    send_sms(config['river']['warn_sms_list'], normal_sms_text)
                    global_vars.river_data["warning_active"] = False
        pass

    except Exception as e:
        logger.error("River task failed: " + str(e))
        pass
