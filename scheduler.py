import time
import schedule
from vedirect_interface import check_load_state,check_batt_voltage
from relays import relay_auto_timeout,relay_reminder_timeout,get_relay_data
from huawei_interface import get_modem_data,connection_checker
from sensors import init_sensors,get_sensor_data # ,get_bm280_data,get_tsl2561_data,get_lis3dh_data,get_gps_data
from environment_agency import init_river,check_river
from sun import get_new_sun_data,update_sun_data
from pico_ups import setup_ups,get_ups_data
from weather import get_weather_forecast
import global_vars
import logging
import colorlog

logger = colorlog.getLogger(__name__)
logger.addHandler(global_vars.file_handler)
logger.addHandler(global_vars.handler)
logger.setLevel(global_vars.log_level)

run_scheduler = True

def setup_scheduler():
    logger.info("Starting modem task")
    schedule.every().second.do(get_modem_data)
    logger.info("Setting up sensors")
    init_sensors()
    logger.info("Starting sensor task")
    schedule.every().second.do(get_sensor_data)
    """
    logger.info("Starting bme280 task")
    schedule.every().second.do(get_bme280_data)
    logger.info("Starting tsl2561 task")
    schedule.every().second.do(get_tsl2561_data)
    logger.info("Starting lis3dh task")
    schedule.every().second.do(get_lis3dh_data)
    logger.info("Starting gps task")
    schedule.every().second.do(get_gps_data)
    """
    logger.info("Starting relay data task")
    schedule.every().second.do(get_relay_data)
    logger.info("Starting relay auto timeout task")
    schedule.every().second.do(relay_auto_timeout)
    logger.info("Starting relay reminder timeout task")
    schedule.every().second.do(relay_reminder_timeout)
    logger.info("Starting connection checker task")
    schedule.every(5).seconds.do(connection_checker)
    logger.info("Starting battery voltage checker task")
    schedule.every(5).seconds.do(check_batt_voltage)
    logger.info("Starting load state checker task")
    schedule.every(5).seconds.do(check_load_state)
    logger.info("Starting river checking task")
    init_river()
    schedule.every(5).minutes.do(check_river)
    logger.info("Starting sun data tasks")
    schedule.every().day.at('00:00').do(get_new_sun_data)
    get_new_sun_data()
    schedule.every().second.do(update_sun_data)
    logger.info("Starting weather forecast task")
    get_weather_forecast()
    schedule.every(15).minutes.do(get_weather_forecast)
    logger.info("Starting PIco UPS data task")
    setup_ups()
    schedule.every().second.do(get_ups_data)
    logger.info("All tasks scheduled!")
    pass


def loop_scheduler():
    logging.getLogger('schedule').setLevel(logging.WARNING)
    logger.info("Starting scheduler")
    setup_scheduler()
    while run_scheduler:
        try:
            schedule.run_pending()
        except Exception as e:
            logger.error("Scheduled task failed: " + str(e))
        time.sleep(0.05)
    logger.warning("Scheduled tasks stopped")
    pass
