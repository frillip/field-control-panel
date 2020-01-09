import global_vars
from yaml_config import config
from datetime import datetime,timedelta
import pytz
import astral
import logging
import colorlog

handler = colorlog.StreamHandler()
handler.setFormatter(global_vars.log_format)
logger = colorlog.getLogger(__name__)
logger.addHandler(handler)
logger.setLevel(global_vars.log_level)

def get_new_sun_data():
    try:
        now = datetime.now(pytz.timezone(config['field']['timezone']))
        logger.info("Getting new sun data for " + now.strftime("%Y-%m-%d"))

        field = astral.Location(('Field','Countesthorpe',config['field']['latitude'],config['field']['longitude'],config['field']['timezone'],config['field']['elevation']))
        sun = field.sun()

        for state in sun:
            global_vars.sun_data[state] = sun[state].replace(tzinfo=None).isoformat()
        logger.info("Sunrise: "+sun['sunrise'].strftime("%H:%M"))
        logger.info("Sunset: "+sun['sunset'].strftime("%H:%M"))

        global_vars.sun_data['golden_hour_start'] = field.golden_hour(direction = astral.SUN_SETTING)[0].replace(tzinfo=None).isoformat()
        global_vars.sun_data['golden_hour_end'] = field.golden_hour(direction = astral.SUN_SETTING)[1].replace(tzinfo=None).isoformat()

        next_sun = field.sun(now+timedelta(days=1))
        global_vars.sun_data['next']['sunrise'] = next_sun['sunrise'].replace(tzinfo=None).isoformat()
        global_vars.sun_data['next']['sunset'] = next_sun['sunset'].replace(tzinfo=None).isoformat()

        update_sun_data()
        pass

    except Exception as e:
        logger.error("Failed getting new sun data: "+str(e))
        pass

def update_sun_data():
    try:
        now = datetime.now(pytz.timezone(config['field']['timezone']))

        field = astral.Location(('Field','Countesthorpe',config['field']['latitude'],config['field']['longitude'],config['field']['timezone'],config['field']['elevation']))
        sun = field.sun()

        if ( now > sun['sunrise'] ) and ( now < sun['sunset'] ):
            global_vars.sun_data['daylight'] = True
        else:
            global_vars.sun_data['daylight'] = False

        if global_vars.sun_data['daylight']:
            global_vars.sun_data['time_to_sunset'] = (sun['sunset'] - now).seconds
        else:
            global_vars.sun_data['time_to_sunset'] = 0

        if now > sun['dusk']:
            global_vars.sun_data['state'] = 'night'
        elif now > sun['sunset']:
            global_vars.sun_data['state'] = 'dusk'
        elif now > sun['sunrise']:
            global_vars.sun_data['state'] = 'day'
        elif now > sun['dawn']:
            global_vars.sun_data['state'] = 'dawn'
        else:
            global_vars.sun_data['state'] = 'night'

        next_sun = field.sun(now+timedelta(days=1))
        if not global_vars.sun_data['daylight']:
            if sun['sunrise'] > now:
                global_vars.sun_data['time_to_sunrise'] = (sun['sunrise'] - now).seconds
            else:
                global_vars.sun_data['time_to_sunrise'] = (next_sun['sunrise'] - now).seconds
        else:
            global_vars.sun_data['time_to_sunrise'] = 0

        global_vars.sun_data['solar_elevation'] = round(field.solar_elevation(),1)
        global_vars.sun_data['solar_azimuth'] = round(field.solar_azimuth(),1)
        global_vars.sun_data['solar_zenith'] = round(field.solar_zenith(),1)
        pass

    except Exception as e:
        logger.error("Failed calculating updated sun data: "+str(e))
        pass
