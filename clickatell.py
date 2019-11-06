import requests
import time
import user_data

api_url = "https://api.clickatell.com/rest/message"

def send_sms(dest_number, message_str):

    global api_url

    headers = {}
    headers["content-type"] = "application/json"
    headers["X-Version"] = "1"
    headers["Authorization"] = "Bearer " + user_data.sms_api_key

    payload = {}
    payload["to"] = dest_number
    payload["from"] = "SHEEPNET"
    payload["text"] = message_str
    # payload["type"] = "flash" #Probably don't want flash, but maybe in the future?

    r = requests.post(api_url, headers=headers, json=payload)
    if r.status_code == 202:
        return True
    else:
        return False

