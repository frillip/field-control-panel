import time
import schedule
from megaio_get_data import get_relay_data
from megaio_set_relays import relay_auto_timeout
from e3372_interface import get_modem_data,connection_checker
from bme_env_data import get_bme_data
from environment_agency import init_river,check_river
import global_vars
import logging
import colorlog

handler = colorlog.StreamHandler()
handler.setFormatter(global_vars.log_format)
logger = colorlog.getLogger(__name__)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

def setup_scheduler():
    logger.info("Starting modem task")
    schedule.every().second.do(get_modem_data)
    logger.info("Starting bme280 task")
    schedule.every().second.do(get_bme_data)
    logger.info("Starting relay data task")
    schedule.every().second.do(get_relay_data)
    logger.info("Starting relay auto timeout task")
    schedule.every().second.do(relay_auto_timeout)
    logger.info("Starting connection checker task")
    schedule.every(5).seconds.do(connection_checker)
    logger.info("Starting river checking tasks")
    init_river()
    schedule.every().hour.at(':01').do(check_river)
    schedule.every().hour.at(':16').do(check_river)
    schedule.every().hour.at(':31').do(check_river)
    schedule.every().hour.at(':46').do(check_river)
    logger.info("All tasks scheduled!")
    pass


def loop_scheduler():
    logging.getLogger('schedule').setLevel(logging.WARNING)
    logger.info("Starting scheduler")
    setup_scheduler()
    while True:
        try:
            schedule.run_pending()
        except Exception as e:
            logger.error("Scheduled task failed: " + str(e))
        time.sleep(0.1)
    pass # Should never get here...
