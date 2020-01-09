import yaml
from os import path
import global_vars
import user_data
import logging
import colorlog

handler = colorlog.StreamHandler()
handler.setFormatter(global_vars.log_format)
logger = colorlog.getLogger(__name__)
logger.setLevel(global_vars.log_level)
logger.addHandler(handler)

# Which file is the config file?
config_file = 'config.yaml'

# Initialise the config dict
config = {}

# Variable to track if config is loaded successfully or not
config['loaded'] = False

# Define what is required, and what is optional (as well as default value if it is missing)
megaio = {
'req': [],
'opt': {
'stack_id': 0
}}

relay = {
'req': ['enabled', 'name'],
'opt': {
'invert': False,
'auto_off': False,
'auto_on': False,
'auto_timeout': 0,
}}

field = {
'req': ['latitude', 'longitude'],
'opt': {
'elevation': 0,
'timezone': 'Europe/London',
}}

bme = {
'req': [],
'opt': {
'i2c_port': 1,
'i2c_address': 0x76, # Most sensors are 0x76
}}

mppt = {
'req': ['tty_dev'],
'opt': {
'baudrate': 19200, # Default VE.Direct speed
}}

bmv = {
'req': ['tty_dev'],
'opt': {
'baudrate': 19200, # Default VE.Direct speed
'warn_enable': False,
'warn_sms_list': [],
}}

e3372 = {
'req': ['dongle_ip'],
'opt': {
}}

river = {
'req': ['api_url', 'api_station_url'],
'opt': {
'high': 10.0,
'high_warn': 10.0,
'warn_enable': False,
'warn_sms_list': [],
}}

met_office = {
'req': ['api_url', 'api_key'],
'opt': {
}}

clickatell = {
'req': ['api_key'],
'opt': {
'sender_name': 'SHEEPNET',
}}

config_structure = {
'megaio' : megaio,
'relay': relay,
'field': field,
'bme': bme,
'mppt': mppt,
'bmv': bmv,
'e3372': e3372,
'river': river,
'met_office': met_office,
'clickatell': clickatell,
}


def load_config():
    global config
    if True:
#    try:
        logger.info('Loading config')
        # Check if the file exists first
        if path.exists(config_file):
            # Open an load the yaml if it does
            with open(config_file, 'r') as file:
                logger.info('Opened '+config_file)
                loaded_yaml = yaml.safe_load(file)
        else:
            # Warn if it doesn't
            logger.error('No config file found!')
            pass

        # Load the config data one block at a timea
        for config_block in loaded_yaml:

            config[config_block] = {}
            logger.info('Loading '+config_block+' config')

            # Relays are special because they have moar levels
            if config_block == 'relay':
            # For each relay
                for relay_id in global_vars.relay_data:
                    try:
                        # If it's enabled in the config, load the data
                        if loaded_yaml['relay'][relay_id]['enabled']:
                            config['relay'][relay_id] = load_config_block(relay,loaded_yaml['relay'][relay_id])
                        # Otherwise mark as disabled
                        else:
                            config['relay'][relay_id] = {}
                            config['relay'][relay_id]['enabled'] = False
                    # If we have missing keys, it's probably because the yaml is incomplete!
                    except KeyError:
                        logger.error('Relay '+str(relay_id)+' not properly configured!')
                        pass

                # Loaded all relay data, so generate the mapping
                generate_relay_map()

            elif config_block in config_structure:
                config[config_block] = load_config_block(config_structure[config_block],loaded_yaml[config_block])

            else:
                logger.warning('Unrecognised config block '+config_block+' not loaded!')

        # This will disappear once other parts are rewritten
        # to use the config options rather than global_vars
        # hence why it is is separate to the above
        global_vars.relay_data = config['relay']

        # If we get here we have successfully loaded the config!
        config['loaded'] = True

#    except Exception as e:
#        logger.error('Unhandled exception whilst loading config: ' + str(e))

    pass

def load_config_block(config_params, config_block):
    loaded_config_block = {}

    for attr in config_params['req']:
        if config_block.get(attr):
            loaded_config_block[attr] = config_block[attr]
        else:
            raise KeyError('Missing required configuration parameter: '+attr)

    # Optional attributes
    for attr in config_params['opt']:
        # If they exist populate the data
        if config_block.get(attr):
            loaded_config_block[attr] = config_block[attr]
        # If not, populate the default
        else:
            loaded_config_block[attr] = config_params['opt'][attr]

    return loaded_config_block

def generate_relay_map():
    try:
        logger.info('Generating relay mappings')
        for relay_id in config['relay']:
            if config['relay'][relay_id]['enabled']:
                relay_name = config['relay'][relay_id]['name']
                global_vars.relay_map[relay_name] = relay_id
                global_vars.relay_timestamp[relay_id] = 0
    except Exception as e:
        # Error has occurred, log it
        logger.error('Failed to generate relay mapping: ' + str(e))

