import requests
from xml.etree import ElementTree

dongle_ip = "192.168.8.1"

def get_auth_data():

    global dongle_ip
    token_info_api_url="http://" + dongle_ip + "/api/webserver/SesTokInfo"

    token_response = requests.get(token_info_api_url)
    print(token_response.cookies)
    print(token_response.content)
    token_tree = ElementTree.fromstring(token_response.content)

    token_secret=token_tree.find("TokInfo").text

    session_id=token_tree.find("SesInfo").text
#    session_id=session_id_raw[10:] # Remove the first 10 characters ("SessionID=")
# Don't do that you melt

    auth_data = { "session_id": session_id, "token_secret": token_secret }

    return auth_data


def send_sms(dest,message):

    global dongle_ip
    send_sms_api_url="http://" + dongle_ip + "/api/sms/send-sms"

    auth_data=get_auth_data()

    print(auth_data['session_id'])
    print(auth_data['token_secret'])

    headers = {"Content-Type": "text/xml; charset=UTF-8",
               "Cookie": auth_data['session_id'],
               "__RequestVerificationToken": auth_data['token_secret']}

    print(headers)

    xml_data = """<?xml version='1.0' encoding='UTF-8'?>
<request><Index>-1</Index><Phones><Phone>""" + dest + \
"""</Phone></Phones><Sca></Sca><Content>""" + message + \
"""</Content><Length>-1</Length><Reserved>1</Reserved>
<Date>-1</Date></request>"""

    print(xml_data)

    sms_response = requests.post(send_sms_api_url, data=xml_data, headers=headers).text

    return sms_response

#def read_sms(message_no) # future function to read SMS from device for balance notification and other useful things
