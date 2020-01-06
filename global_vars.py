from datetime import datetime
import logging
import colorlog

log_format = colorlog.ColoredFormatter(
        "%(asctime)s %(log_color)s[%(levelname)s]%(reset)s %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
        log_colors={
        'DEBUG': 'cyan',
        'INFO': 'green',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'red,bg_white',
        })

log_level = logging.INFO

handler = colorlog.StreamHandler()
handler.setFormatter(log_format)
logger = colorlog.getLogger(__name__)
logger.addHandler(handler)
logger.setLevel(log_level)

# Will be moved to YAML eventually

timezone = 'Europe/London'
sun_data = {}
sun_data['next'] = {}

field_latitude = 52.553
field_longitude = -1.171
field_elevation = 0

weather_data = {}
weather_data['site'] = {}

bme_data = {}

mppt_data = {}
mppt_data["batt"] = {}
mppt_data["load"] = {}
mppt_data["pv"] = {}

bmv_data = {}
bmv_data["batt"] = {}
bmv_data["stats"] = {}

modem_data = {}
modem_data["data_usage"] = {}
river_data = {}

relay_data = {}
relay_data[1] = {}
relay_data[1]['enabled'] = True
relay_data[1]['name'] = "fence"
relay_data[1]['raw_state'] = False
relay_data[1]['invert'] = True
relay_data[1]['state'] = relay_data[1]['raw_state'] ^ relay_data[1]['invert']
relay_data[1]['auto_on'] = False
relay_data[1]['auto_off'] = False
relay_data[1]['auto_timeout'] = 0
relay_data[1]['last_state_change'] = datetime.now().replace(microsecond=0).isoformat()

relay_data[2] = {}
relay_data[2]['enabled'] = True
relay_data[2]['name'] = "cameras"
relay_data[2]['raw_state'] = False
relay_data[2]['invert'] = False
relay_data[2]['state'] = relay_data[2]['raw_state'] ^ relay_data[2]['invert']
relay_data[2]['auto_on'] = False
relay_data[2]['auto_off'] = True
relay_data[2]['auto_timeout'] = 300
relay_data[2]['last_state_change'] = datetime.now().replace(microsecond=0).isoformat()

relay_data[3] = {}
relay_data[3]['enabled'] = True
relay_data[3]['name'] = "lighting"
relay_data[3]['raw_state'] = False
relay_data[3]['invert'] = False
relay_data[3]['state'] = relay_data[3]['raw_state'] ^ relay_data[3]['invert']
relay_data[3]['auto_on'] = False
relay_data[3]['auto_off'] = False
relay_data[3]['auto_timeout'] = 0
relay_data[3]['last_state_change'] = datetime.now().replace(microsecond=0).isoformat()

relay_data[4] = {}
relay_data[4]['enabled'] = False
relay_data[5] = {}
relay_data[5]['enabled'] = False
relay_data[6] = {}
relay_data[6]['enabled'] = False
relay_data[7] = {}
relay_data[7]['enabled'] = False
relay_data[8] = {}
relay_data[8]['enabled'] = False

relay_map = {}
relay_timestamp = {}

try:
    for relay_id in relay_data:
        if relay_data[relay_id]['enabled']:
            relay_name = relay_data[relay_id]['name']
            relay_map[relay_name] = relay_id
            relay_timestamp[relay_id] = 0
except Exception as e:
    # Error has occurred, log it
    logger.error("Failed to generate relay mapping: " + str(e))

