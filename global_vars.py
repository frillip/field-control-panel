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
mppt_data = {}
mppt_data["batt"] = {}
mppt_data["load"] = {}
mppt_data["pv"] = {}

bmv_data = {}
bmv_data["batt"] = {}
bmv_data["stats"] = {}

modem_data = {}
modem_data["data_usage"] = {}
modem_data["data_usage"]["current"] = {}
modem_data["data_usage"]["month"] = {}
modem_data["data_usage"]["total"] = {}

