import requests
from yaml_config import config
import global_vars
from datetime import datetime
from sms_sender import send_sms
import logging
import colorlog

handler = colorlog.StreamHandler()
handler.setFormatter(global_vars.log_format)
logger = colorlog.getLogger(__name__)
logger.addHandler(handler)
logger.setLevel(global_vars.log_level)

river_data = {}
river_data['last'] = {}

def init_river():
    try:
        logger.info('Initialising river data from Environment Agency')
        resp = requests.get(config['river']['api_station_url'])
        river_data['id'] = resp.json()['items']['stationReference']
        river_data['name'] = resp.json()['items']['riverName']
        river_data['level'] = resp.json()['items']['measures']['latestReading']['value']
        river_data['timestamp'] = resp.json()['items']['measures']['latestReading']['dateTime'][:-1]
        # If this hasn't been set pull from the retrieved JSON
        if config['river']['high_warn']:
            river_data['high_warn'] = config['river']['high_warn']
            river_data['high'] = config['river']['high']
        else:
            river_data['high_warn'] = resp.json()['items']['stageScale']['typicalRangeHigh']
            river_data['high'] = river_data['high_warn'] - 0.15 # 0.15 is generally a good guess for hysteresis

        check_river()

    except Exception as e:
        logger.error('River init failed: ' + str(e))


def check_river():

    try:
        resp = requests.get(config['river']['api_url'])
        # If the timestamps have changed, we have a new reading, so process it
        if resp.json()['items']['latestReading']['dateTime'][:-1] != river_data['timestamp']:
            river_data['last']['timestamp'] = river_data['timestamp']
            river_data['timestamp'] = resp.json()['items']['latestReading']['dateTime'][:-1]

            river_data['last']['level'] = river_data['level']
            river_data['level'] = resp.json()['items']['latestReading']['value']

            if river_data['level'] > river_data['last']['level']:
                river_data['status'] = 'rising'
            elif river_data['level'] < river_data['last']['level']:
                river_data['status'] = 'falling'
            else:
                river_data['status'] = 'steady'

            human_datetime = datetime.now().strftime('%d/%m/%Y %H:%M')
            now_iso_stamp = datetime.now().replace(microsecond=0).isoformat()
            if river_data['level'] > river_data['last']['high_level']:
                river_data['last']['high_level'] = river_data['level']
                river_data['last']['high'] = river_data['timestamp']

            if config['river']['warn_enable']:
                if river_data['level'] > river_data['high_warn']:
                    if not river_data['warning_active'] or ( river_data['warning_active'] and river_data['level'] > ( river_data['last']['warn_level'] + 0.1) ):
                        if not river_data['warning_active']:
                            logger.critical('River level high! '+str(river_data['level'])+'m. Sending alert SMS!')
                            warn_sms_text = human_datetime + ': River level high! '+str(river_data['level'])+'m'
                        else:
                            logger.critical('River level rising! '+str(river_data['level'])+'m. Sending alert SMS!')
                            warn_sms_text = human_datetime + ': River level rising! '+str(river_data['level'])+'m'
                        send_sms(config['river']['warn_sms_list'], warn_sms_text)
                        logger.critical('Alerts sent')
                        river_data['last']['warn_level'] = river_data['level']
                        river_data['last']['high_level'] = river_data['level']
                        river_data['warning_active'] = True
                        river_data['last']['warn'] = now_iso_stamp

                if river_data['warning_active'] and river_data['level'] < river_data['high']:
                    logger.warning('River returned to normal levels')
                    normal_sms_text = human_datetime + ': River level returned to normal. '+str(river_data['level'])+'m'
                    send_sms(config['river']['warn_sms_list'], normal_sms_text)
                    river_data['warning_active'] = False
        pass

    except Exception as e:
        logger.error('River task failed: ' + str(e))
        pass
