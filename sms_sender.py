import huawei_interface
import clickatell

def send_sms(dest_list, sms_text):
    if huawei_interface.net_connected():
        clickatell.send_sms(dest_list, sms_text)
    else:
        for dest in dest_list:
            huawei_interface.send_sms(dest, sms_text)
