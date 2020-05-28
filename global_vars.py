from datetime import datetime
import logging
from logging.handlers import RotatingFileHandler
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

log_file_format = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
        )

log_level = logging.INFO

log_file = '/var/log/field/field.log'

file_handler = RotatingFileHandler(log_file, maxBytes=10000000, backupCount=10)
file_handler.setFormatter(log_file_format)

handler = colorlog.StreamHandler()
handler.setFormatter(log_format)

logger = colorlog.getLogger(__name__)
logger.addHandler(handler)
logger.addHandler(file_handler)
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

