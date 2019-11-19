import e3372_interface
import clickatell

def send_sms(dest_list, sms_text):
    if e3372_interface.net_connected():
        clickatell.send_sms(dest_list, sms_text)
    else:
        for dest in dest_list:
            e3372_interface.send_sms(dest, sms_text)
