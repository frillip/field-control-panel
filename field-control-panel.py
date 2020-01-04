from threading import Thread
from time import sleep
import global_vars
import scheduler
from e3372_interface import get_modem_data,send_connection_req,net_connected
import panel_web_app
import vedirect_interface
import logging
import colorlog

def main():
    print("*******************************************************************************************\n\n\n")
    print("Welcome...")
    try:
        f = open('ascii_logo.txt','r')
        ascii_logo = f.read()
        f.close()
        print(ascii_logo)
    except:
        pass
    print("... to Jurassic Park\n\n\n")
    print("*******************************************************************************************")
    handler = colorlog.StreamHandler()
    handler.setFormatter(global_vars.log_format)
    logger = colorlog.getLogger("main")
    logger.setLevel(global_vars.log_level)
    logger.addHandler(handler)
    logger.info("Starting Jurassic Park Control System")

    logger.info("Connecting to LTE")
    get_modem_data()
    while not net_connected():
        send_connection_req()
        sleep(1)
        get_modem_data()

    logger.info("Connected!")

    t1 = Thread(target=vedirect_interface.mppt_loop)
    t2 = Thread(target=vedirect_interface.bmv_loop)
    t3 = Thread(target=scheduler.loop_scheduler)
    t4 = Thread(target=panel_web_app.run_server, args=(panel_web_app.run_web_app(),))
    t1.start()
    t2.start()
    t3.start()
    t4.start()


if __name__ == '__main__':
    main()
