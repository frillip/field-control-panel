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

# Global var for if config/save state has been loaded
config_loaded = False
last_state_loaded = False

# Set up dicts for holding data
sun_data = {}
sun_data['next'] = {}

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
relay_data[2] = {}
relay_data[3] = {}
relay_data[4] = {}
relay_data[5] = {}
relay_data[6] = {}
relay_data[7] = {}
relay_data[8] = {}
relay_map = {}
relay_timestamp = {}

