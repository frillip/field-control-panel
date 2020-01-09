import requests
import global_vars
from yaml_config import config
import logging
import colorlog

handler = colorlog.StreamHandler()
handler.setFormatter(global_vars.log_format)
logger = colorlog.getLogger(__name__)
logger.addHandler(handler)
logger.setLevel(global_vars.log_level)

# API url is fixed for clickatell, so not much point in putting in config
api_url = "https://api.clickatell.com/rest/message"

def send_sms(dest_list, message_str):

    headers = {}
    headers["content-type"] = "application/json"
    headers["X-Version"] = "1"
    headers["Authorization"] = "Bearer " + config['clickatell']['api_key']

    payload = {}
    payload["to"] = dest_list
    payload["from"] = config['clickatell']['sender_name']
    payload["text"] = message_str
    # payload["type"] = "flash" #Probably don't want flash, but maybe in the future?

    try:
        r = requests.post(api_url, headers=headers, json=payload)
        if r.status_code == 202:
            for number in dest_list:
                logger.warning("SMS sent to " + number)
            return True
        else:
            for number in dest_list:
                logger.error("Failed to send SMS to: " + number)
            return False

    except Exception as e:
        logger.error("Clickatell sms failed: " + str(e))
        return False

