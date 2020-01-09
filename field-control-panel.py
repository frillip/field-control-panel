from threading import Thread
from time import sleep
import signal
import sys
import global_vars
import scheduler
from e3372_interface import get_modem_data,send_connection_req,net_connected
import panel_web_app
import vedirect_interface
import yaml_save_state
import yaml_config
import logging
import colorlog

handler = colorlog.StreamHandler()
handler.setFormatter(global_vars.log_format)
logger = colorlog.getLogger("main")
logger.setLevel(global_vars.log_level)
logger.addHandler(handler)

mppt_loop_thread = Thread(target=vedirect_interface.mppt_loop)
bmv_loop_thread = Thread(target=vedirect_interface.bmv_loop)
scheduler_thread = Thread(target=scheduler.loop_scheduler)
web_app_thread = Thread(target=panel_web_app.run_server, args=(panel_web_app.run_web_app(),))

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
    logger.info("Starting Jurassic Park Control System")
    logger.info("Registering SIGINT handler")
    signal.signal(signal.SIGINT, signal_handler)
    yaml_config.load_config()
    if not yaml_config.config['loaded']:
        logger.error("Config not loaded! Exiting...")
        sys.exit(1)
    yaml_save_state.load_last_saved_state()
    logger.info("Connecting to LTE")
    get_modem_data()
    while not net_connected():
        send_connection_req()
        sleep(1)
        get_modem_data()

    logger.info("Connected!")

    mppt_loop_thread.start()
    bmv_loop_thread.start()
    scheduler_thread.start()
    # Wait for some data before starting the webserver
    sleep(3)
    web_app_thread.start()

    while True:
        sleep(0.5)


def signal_handler(sig, frame):
    logger.warning("Caught CTRL-C interrupt! Stopping...")
    yaml_save_state.save_running_state()
    logger.warning("Stopping scheduled tasks")
    scheduler.run_scheduler = False
    logger.warning("Stopping VE.Direct data loops")
    vedirect_interface.run_mppt_vedirect_loop = False
    vedirect_interface.run_bmv_vedirect_loop = False
    logger.warning("Stopping webapp server")
    panel_web_app.stop_server()
    sys.exit(0)


if __name__ == '__main__':
    main()
