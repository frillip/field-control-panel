from e3372_interface import get_modem_data,send_connection_req
from time import sleep

while True:
    modem_data = get_modem_data()
    if modem_data["connected"]:
        print("Already connected, doing nothing for 5s...")
    else:
        print("Not connected. Sending connection request...")
        if send_connection_req():
            print("Done!")
        else:
            print("Something went wrong!")
    sleep(5)
