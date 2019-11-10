import requests
import time
import user_data
import logging

api_url = "https://api.clickatell.com/rest/message"

def send_sms(dest_list, message_str):

    global api_url
    logger = logging.getLogger("clicktall sms")

    headers = {}
    headers["content-type"] = "application/json"
    headers["X-Version"] = "1"
    headers["Authorization"] = "Bearer " + user_data.sms_api_key

    payload = {}
    payload["to"] = dest_list
    payload["from"] = "SHEEPNET"
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
                logger.warning("Failed to send SMS to: " + number)
            return False

    except Exception as e:
        logger.error("Clickatell sms failed: " + str(e))
        return False

