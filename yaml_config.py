import yaml
import global_vars
import logging
import colorlog

handler = colorlog.StreamHandler()
handler.setFormatter(global_vars.log_format)
logger = colorlog.getLogger(__name__)
logger.setLevel(global_vars.log_level)
logger.addHandler(handler)

# Which file is the config file?
config_file = 'config.yaml'

# Variable to track if config is loaded successfully or not
config_loaded = False

def generate_relay_map():
    try:
        for relay_id in global_vars.relay_data:
            if global_vars.relay_data[relay_id]['enabled']:
                relay_name = global_vars.relay_data[relay_id]['name']
                global_vars.relay_map[relay_name] = relay_id
                global_vars.relay_timestamp[relay_id] = 0
    except Exception as e:
        # Error has occurred, log it
        logger.error("Failed to generate relay mapping: " + str(e))

