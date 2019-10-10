import requests
import xmltodict

dongle_ip = "192.168.8.1"

def get_auth_data():

    global dongle_ip
    token_info_api_url="http://" + dongle_ip + "/api/webserver/SesTokInfo"

    token_resp = requests.get(token_info_api_url)
    if "SessionID" in token_resp.text:

        token=xmltodict.parse(token_resp.content)['response']

        token_secret=token["TokInfo"]
        session_id=token["SesInfo"]

        auth_data = { "session_id": session_id, "token_secret": token_secret }
        return auth_data

    else:
        return False


def construct_auth_headers(auth_data):

    headers = {"Content-Type": "text/xml; charset=UTF-8",
               "Cookie": auth_data['session_id'],
               "__RequestVerificationToken": auth_data['token_secret']}

    return headers

def get_modem_data():

    global dongle_ip
    get_dev_info_api_url="http://" + dongle_ip + "/api/device/information"
    get_mon_stat_api_url="http://" + dongle_ip + "/api/monitoring/status"
    get_mon_traf_api_url="http://" + dongle_ip + "/api/monitoring/traffic-statistics"

    modem_data = {}

    auth_data=get_auth_data()
    if auth_data:
        headers = construct_auth_headers(auth_data)

    dev_info_resp = requests.get(get_dev_info_api_url, headers=headers)
    mon_stat_resp = requests.get(get_mon_stat_api_url, headers=headers)
    mon_traf_resp = requests.get(get_mon_traf_api_url, headers=headers)

    if "DeviceName" in dev_info_resp.text:
        dev_info = xmltodict.parse(dev_info_resp.content)['response']
    else:
        return False

    modem_data["name"] = dev_info["DeviceName"]
    modem_data["network_type"] = dev_info["workmode"]

    if "ServiceStatus" in mon_stat_resp.text:
        mon_stat = xmltodict.parse(mon_stat_resp.content)['response']
    else:
        return False

    modem_data["signal_strength"] = int(mon_stat["SignalIcon"])
    modem_data["wan_ip"] = mon_stat["WanIPAddress"]
    if mon_stat["ServiceStatus"]:
        modem_data["connected"] = True
    else:
        modem_data["connected"] = False


    if "CurrentConnectTime" in mon_traf_resp.text:
        mon_traf = xmltodict.parse(mon_traf_resp.content)['response']
    else:
        return False

    data_usage = {}
    data_usage["data_up"] = int(mon_traf["CurrentUpload"])
    data_usage["data_down"] = int(mon_traf["CurrentDownload"])
    data_usage["data_rate_up"] = int(mon_traf["CurrentUploadRate"])
    data_usage["data_rate_down"] = int(mon_traf["CurrentDownloadRate"])
    data_usage["data_total_up"] = int(mon_traf["TotalUpload"])
    data_usage["data_total_down"] = int(mon_traf["TotalDownload"])

    modem_data["data_usage"] = data_usage

    modem_data["connected_time"] = int(mon_traf["CurrentConnectTime"])
    modem_data["connected_total_time"] = int(mon_traf["TotalConnectTime"])

    return modem_data


def send_sms(dest,message):

    global dongle_ip
    send_sms_api_url="http://" + dongle_ip + "/api/sms/send-sms"

    auth_data=get_auth_data()
    if auth_data:
        headers = construct_auth_headers(auth_data)

    xml_data = """<?xml version='1.0' encoding='UTF-8'?>
<request><Index>-1</Index><Phones><Phone>""" + dest + \
"""</Phone></Phones><Sca></Sca><Content>""" + message + \
"""</Content><Length>-1</Length><Reserved>1</Reserved>
<Date>-1</Date></request>"""

    send_sms_resp = requests.post(send_sms_api_url, data=xml_data, headers=headers)
    send_sms_xml = ElementTree.fromstring(send_sms_resp.content)

    print(send_sms_xml)

    if send_sms_xml.text == "OK":
        return True
    else:
        return False

#def read_sms(message_no) # future function to read SMS from device for balance notification and other useful things
