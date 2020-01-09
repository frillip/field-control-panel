import requests
import xmltodict
from time import sleep
import global_vars
import global_vars
from yaml_config import config
import logging
import colorlog

handler = colorlog.StreamHandler()
handler.setFormatter(global_vars.log_format)
logger = colorlog.getLogger(__name__)
logger.addHandler(handler)
logger.setLevel(global_vars.log_level)


def get_auth_data():

    token_info_api_url="http://" + config['e3372']['dongle_ip'] + "/api/webserver/SesTokInfo"

    try:
        token_resp = requests.get(token_info_api_url)
        if "SessionID" in token_resp.text:

            token=xmltodict.parse(token_resp.content)['response']

            token_secret=token["TokInfo"]
            session_id=token["SesInfo"]

            auth_data = { "session_id": session_id, "token_secret": token_secret }
            return auth_data

        else:
            logger.error("Modem auth data request failed: " + token_resp.text)
            return False

    except Exception as e:
        logger.error("Modem auth data request failed: " + str(e))


def construct_auth_headers(auth_data):

    headers = {"Content-Type": "text/xml; charset=UTF-8",
               "Cookie": auth_data['session_id'],
               "__RequestVerificationToken": auth_data['token_secret']}

    return headers

def send_connection_req():

    req_connection_api_url="http://" + config['e3372']['dongle_ip'] + "/api/dialup/dial"
    connection_req_xml = '<?xml version="1.0" encoding="UTF-8"?><request><Action>1</Action></request>'

    try:
        logger.warning("Sending connection request to modem")
        auth_data=get_auth_data()
        if auth_data:
            headers = construct_auth_headers(auth_data)

        post_req = requests.post(req_connection_api_url, headers=headers, data=connection_req_xml)

        if "OK" in post_req.text:
            logger.warning("Connection request made OK!")
            return True
        else:
            logger.error("Modem connection request failed: " + post_req.text)
            return False

    except Exception as e:
        logger.error("Modem connection request failed: " + str(e))

def send_reboot_req():

    req_reboot_api_url="http://" + config['e3372']['dongle_ip'] + "/api/device/control"
    reboot_req_xml = '<?xml version="1.0" encoding="UTF-8"?><request><Control>1</Control></request>'

    try:
        logger.warning("Sending reboot request to modem")
        auth_data=get_auth_data()
        if auth_data:
            headers = construct_auth_headers(auth_data)

        post_req = requests.post(req_reboot_api_url, headers=headers, data=reboot_req_xml)

        if "OK" in post_req.text:
            logger.warning("Modem rebooting!")
            return True
        else:
            logger.error("Modem reboot request failed: " + post_req.text)
            return False

    except Exception as e:
        logger.error("Modem reboot request failed: " + str(e))


def get_modem_data():

    get_dev_info_api_url="http://" + config['e3372']['dongle_ip'] + "/api/device/information"
    get_mon_stat_api_url="http://" + config['e3372']['dongle_ip'] + "/api/monitoring/status"
    get_mon_traf_api_url="http://" + config['e3372']['dongle_ip'] + "/api/monitoring/traffic-statistics"

    try:
        auth_data=get_auth_data()
        if auth_data:
             headers = construct_auth_headers(auth_data)

        dev_info_resp = requests.get(get_dev_info_api_url, headers=headers)

        if "DeviceName" in dev_info_resp.text:
            dev_info = xmltodict.parse(dev_info_resp.content)['response']

            global_vars.modem_data["name"] = dev_info["DeviceName"]
        else:
            logger.error("Modem task failed: could not retrieve " + get_dev_info_api_url)

        mon_stat_resp = requests.get(get_mon_stat_api_url, headers=headers)

        if "ConnectionStatus" in mon_stat_resp.text:
            mon_stat = xmltodict.parse(mon_stat_resp.content)['response']

            global_vars.modem_data["signal_strength"] = int(mon_stat["SignalIcon"])
            global_vars.modem_data["wan_ip"] = mon_stat["WanIPAddress"]
            net_type_ex=int(mon_stat["CurrentNetworkTypeEx"])
            if net_type_ex == 0:
                global_vars.modem_data["network_type"] = "No Service"
            elif net_type_ex == 1:
                global_vars.modem_data["network_type"] = "GSM"
            elif net_type_ex == 2:
                global_vars.modem_data["network_type"] = "GPRS"
            elif net_type_ex == 3:
                global_vars.modem_data["network_type"] = "EDGE"
            elif net_type_ex == 41:
                global_vars.modem_data["network_type"] = "WCDMA"
            elif net_type_ex == 42:
                global_vars.modem_data["network_type"] = "HSDPA"
            elif net_type_ex == 43:
                global_vars.modem_data["network_type"] = "HSUPA"
            elif net_type_ex == 44:
                global_vars.modem_data["network_type"] = "HSPA"
            elif net_type_ex == 45:
                global_vars.modem_data["network_type"] = "HSPA+"
            elif net_type_ex == 46:
                global_vars.modem_data["network_type"] = "HSPA+"
            elif net_type_ex == 62:
                global_vars.modem_data["network_type"] = "HSDPA"
            elif net_type_ex == 63:
                global_vars.modem_data["network_type"] = "HSUPA"
            elif net_type_ex == 64:
                global_vars.modem_data["network_type"] = "HSPA"
            elif net_type_ex == 65:
                global_vars.modem_data["network_type"] = "HSPA+"
            elif net_type_ex == 101:
                global_vars.modem_data["network_type"] = "LTE"
            else:
                global_vars.modem_data["network_type"] = "Unknown"

            if mon_stat["ConnectionStatus"] == "901":
                global_vars.modem_data["connected"] = True
            else:
                global_vars.modem_data["connected"] = False
        else:
            logger.error("Modem task failed: could not retrieve " + get_mon_stat_api_url)

        mon_traf_resp = requests.get(get_mon_traf_api_url, headers=headers)
        if "CurrentConnectTime" in mon_traf_resp.text:
            mon_traf = xmltodict.parse(mon_traf_resp.content)['response']

            global_vars.modem_data["data_usage"]["data_up"] = int(mon_traf["CurrentUpload"])
            global_vars.modem_data["data_usage"]["data_down"] = int(mon_traf["CurrentDownload"])
            global_vars.modem_data["data_usage"]["data_rate_up"] = int(mon_traf["CurrentUploadRate"])
            global_vars.modem_data["data_usage"]["data_rate_down"] = int(mon_traf["CurrentDownloadRate"])
            global_vars.modem_data["data_usage"]["data_total_up"] = int(mon_traf["TotalUpload"])
            global_vars.modem_data["data_usage"]["data_total_down"] = int(mon_traf["TotalDownload"])

            global_vars.modem_data["connected_time"] = int(mon_traf["CurrentConnectTime"])
            global_vars.modem_data["connected_total_time"] = int(mon_traf["TotalConnectTime"])
        else:
            logger.error("Modem task failed: could not retrieve " + get_mon_traf_api_url)

    except Exception as e:
        logger.error("Modem task failed: " + str(e))

    pass


def send_sms(dest,message):

    send_sms_api_url="http://" + config['e3372']['dongle_ip'] + "/api/sms/send-sms"

    try:
        auth_data=get_auth_data()
        if auth_data:
            headers = construct_auth_headers(auth_data)

        xml_data = """<?xml version='1.0' encoding='UTF-8'?>
<request><Index>-1</Index><Phones><Phone>""" + dest + \
"""</Phone></Phones><Sca></Sca><Content>""" + message + \
"""</Content><Length>-1</Length><Reserved>1</Reserved>
<Date>-1</Date></request>"""

        send_sms_resp = requests.post(send_sms_api_url, data=xml_data, headers=headers)

        if "OK" in send_sms_resp.text:
            logger.warning("SMS sent to " + dest)
            return True
        else:
            logger.error("SMS send failed: " + send_sms_resp.text)
            return False

    except Exception as e:
        logger.error("SMS send failed: " + str(e))
        return False


#def read_sms(message_no) # future function to read SMS from device for balance notification and other useful things

def net_connected():
    try:
        if global_vars.modem_data["connected"] and global_vars.modem_data["connected_time"]:
           return True
        else:
           return False
    except Exception as e:
        logger.error("Connection check failed: " + str(e))
        return False

def connection_checker():
    if not net_connected():
        logger.warning("Modem is not connected!")
        send_connection_req()
    pass
