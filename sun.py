import global_vars
from yaml_config import config
from sensors import gps_data
from datetime import datetime,timedelta
import pytz
import astral
import logging
import colorlog

logger = colorlog.getLogger(__name__)
logger.addHandler(global_vars.file_handler)
logger.addHandler(global_vars.handler)
logger.setLevel(global_vars.log_level)

sun_data = {}
sun_data['site'] = {}
sun_data['next'] = {}


def get_new_sun_data():
    try:
        now = datetime.now(pytz.timezone(config['field']['timezone']))
        logger.info("Getting new sun data for " + now.strftime("%Y-%m-%d"))

        # Use the GPS data if enabled and available
        if config['sensors']['gps_enable'] and ( gps_data['mode'] >= 2 ):
            sun_data['site']['latitude'] = gps_data['latitude']
            sun_data['site']['longitude'] = gps_data['longitude']
            sun_data['site']['timezone'] = config['field']['timezone']
            sun_data['site']['elevation'] = gps_data['altitude']
        else:
            sun_data['site']['latitude'] = config['field']['latitude']
            sun_data['site']['longitude'] = config['field']['longitude']
            sun_data['site']['timezone'] = config['field']['timezone']
            sun_data['site']['elevation'] = config['field']['elevation']

        field = astral.Location(('Field','Countesthorpe',sun_data['site']['latitude'],sun_data['site']['longitude'],sun_data['site']['timezone'],sun_data['site']['elevation']))
        sun = field.sun()

        for state in sun:
            sun_data[state] = sun[state].replace(tzinfo=None).isoformat()
        logger.info("Sunrise: "+sun['sunrise'].strftime("%H:%M"))
        logger.info("Sunset: "+sun['sunset'].strftime("%H:%M"))

        next_sun = field.sun(now+timedelta(days=1))
        sun_data['next']['sunrise'] = next_sun['sunrise'].replace(tzinfo=None).isoformat()
        sun_data['next']['sunset'] = next_sun['sunset'].replace(tzinfo=None).isoformat()

        update_sun_data()
        pass

    except Exception as e:
        logger.error("Failed getting new sun data: "+str(e))
        pass

def update_sun_data():
    try:
        now = datetime.now(pytz.timezone(config['field']['timezone']))

        # Use the GPS data if enabled and available
        if config['sensors']['gps_enable'] and ( gps_data['mode'] >= 2 ):
            sun_data['site']['latitude'] = gps_data['latitude']
            sun_data['site']['longitude'] = gps_data['longitude']
            sun_data['site']['timezone'] = config['field']['timezone']
            sun_data['site']['elevation'] = gps_data['altitude']
        else:
            sun_data['site']['latitude'] = config['field']['latitude']
            sun_data['site']['longitude'] = config['field']['longitude']
            sun_data['site']['timezone'] = config['field']['timezone']
            sun_data['site']['elevation'] = config['field']['elevation']

        field = astral.Location(('Field','Countesthorpe',sun_data['site']['latitude'],sun_data['site']['longitude'],sun_data['site']['timezone'],sun_data['site']['elevation']))
        sun = field.sun()

        if ( now > sun['sunrise'] ) and ( now < sun['sunset'] ):
            sun_data['daylight'] = True
        else:
            sun_data['daylight'] = False

        if sun_data['daylight']:
            sun_data['time_to_sunset'] = (sun['sunset'] - now).seconds
        else:
            sun_data['time_to_sunset'] = 0

        if now > sun['dusk']:
            sun_data['state'] = 'night'
        elif now > sun['sunset']:
            sun_data['state'] = 'dusk'
        elif now > sun['sunrise']:
            sun_data['state'] = 'day'
        elif now > sun['dawn']:
            sun_data['state'] = 'dawn'
        else:
            sun_data['state'] = 'night'

        next_sun = field.sun(now+timedelta(days=1))
        if not sun_data['daylight']:
            if sun['sunrise'] > now:
                sun_data['time_to_sunrise'] = (sun['sunrise'] - now).seconds
            else:
                sun_data['time_to_sunrise'] = (next_sun['sunrise'] - now).seconds
        else:
            sun_data['time_to_sunrise'] = 0

        sun_data['solar_elevation'] = round(field.solar_elevation(),1)
        sun_data['solar_azimuth'] = round(field.solar_azimuth(),1)
        sun_data['solar_zenith'] = round(field.solar_zenith(),1)
        pass

    except Exception as e:
        logger.error("Failed calculating updated sun data: "+str(e))
        pass
