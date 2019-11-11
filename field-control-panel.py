from threading import Thread
from time import sleep
import scheduler
import panel_web_app
import vedirect_interface
import logging
import colorlog

def main():
    print("*******************************************************************************************\n\n\n\n\n")
    print("Welcome...")
    print("... to Jurassic Park\n\n\n\n\n")
    print("*******************************************************************************************")
    handler = colorlog.StreamHandler()
    handler.setFormatter(colorlog.ColoredFormatter(
        "%(asctime)s %(log_color)s[%(levelname)s]%(reset)s %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
        log_colors={
        'DEBUG': 'cyan',
        'INFO': 'green',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'red,bg_white',
        }))
    logger = colorlog.getLogger("main")
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    logger.info("Starting Jurassic Park Control System...")

    t1 = Thread(target=vedirect_interface.mppt_loop)
    t2 = Thread(target=scheduler.loop_scheduler)
    t3 = Thread(target=panel_web_app.run_server, args=(panel_web_app.run_web_app(),))
    t1.start()
    t2.start()
    t3.start()


if __name__ == '__main__':
    main()
