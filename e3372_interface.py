import requests
import xmltodict
from time import sleep
import global_vars

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

def send_connection_req():

    global dongle_ip

    req_connection_api_url="http://" + dongle_ip + "/api/dialup/dial"
    connection_req_xml = '<?xml version="1.0" encoding="UTF-8"?><request><Action>1</Action></request>'
    auth_data=get_auth_data()
    if auth_data:
        headers = construct_auth_headers(auth_data)

    post_req = requests.post(req_connection_api_url, headers=headers, data=connection_req_xml)

    if "OK" in post_req.text:
        return True
    else:
        return False

def send_reboot_req():

    global dongle_ip

    req_reboot_api_url="http://" + dongle_ip + "/api/device/control"
    reboot_req_xml = '<?xml version="1.0" encoding="UTF-8"?><request><Control>1</Control></request>'
    auth_data=get_auth_data()
    if auth_data:
        headers = construct_auth_headers(auth_data)

    post_req = requests.post(req_reboot_api_url, headers=headers, data=reboot_req_xml)

    if "OK" in post_req.text:
        return True
    else:
        return False


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

    try:
        if "DeviceName" in dev_info_resp.text:
            dev_info = xmltodict.parse(dev_info_resp.content)['response']

            modem_data["name"] = dev_info["DeviceName"]
        else:
            modem_data["e"]=True

        mon_stat_resp = requests.get(get_mon_stat_api_url, headers=headers)

        if "ConnectionStatus" in mon_stat_resp.text:
            mon_stat = xmltodict.parse(mon_stat_resp.content)['response']
            
            modem_data["signal_strength"] = int(mon_stat["SignalIcon"])
            modem_data["wan_ip"] = mon_stat["WanIPAddress"]
            net_type_ex=int(mon_stat["CurrentNetworkTypeEx"])
            if net_type_ex == 0:
                modem_data["network_type"] = "No Service"
            elif net_type_ex == 1:
                modem_data["network_type"] = "GSM"
            elif net_type_ex == 2:
                modem_data["network_type"] = "GPRS"
            elif net_type_ex == 3:
                modem_data["network_type"] = "EDGE"
            elif net_type_ex == 41:
                modem_data["network_type"] = "WCDMA"
            elif net_type_ex == 42:
                modem_data["network_type"] = "HSDPA"
            elif net_type_ex == 43:
                modem_data["network_type"] = "HSUPA"
            elif net_type_ex == 44:
                modem_data["network_type"] = "HSPA"
            elif net_type_ex == 45:
                modem_data["network_type"] = "HSPA+"
            elif net_type_ex == 46:
                modem_data["network_type"] = "HSPA+"
            elif net_type_ex == 62:
                modem_data["network_type"] = "HSDPA"
            elif net_type_ex == 63:
                modem_data["network_type"] = "HSUPA"
            elif net_type_ex == 64:
                modem_data["network_type"] = "HSPA"
            elif net_type_ex == 65:
                modem_data["network_type"] = "HSPA+"
            elif net_type_ex == 101:
                modem_data["network_type"] = "LTE"
            else:
                modem_data["network_type"] = "Unknown"

            if mon_stat["ConnectionStatus"] == "901":
                modem_data["connected"] = True
            else:
                modem_data["connected"] = False
        else:
            modem_data["e"]=True

        mon_traf_resp = requests.get(get_mon_traf_api_url, headers=headers)
        if "CurrentConnectTime" in mon_traf_resp.text:
            mon_traf = xmltodict.parse(mon_traf_resp.content)['response']

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
        else:
            modem_data["e"]=True

        modem_data["e"]=False
    except:
        modem_data["e"]=True

    global_vars.modem_data = modem_data

    pass


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

    if "OK" in send_sms_resp.text:
        return True
    else:
        return False

#def read_sms(message_no) # future function to read SMS from device for balance notification and other useful things

def net_connected():
    if global_vars.modem_data["connected"] and global_vars.modem_data["connected_time"]:
       return True
    else:
       return False

def connection_checker():
    if not net_connected():
        print("Not connected. Sending connection request...")
        if send_connection_req():
            print("Done!")
        else:
            print("Something went wrong!")
    pass
