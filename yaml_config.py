import yaml
from os import path
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

huawei = {
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

clickatell = {
'req': ['api_key'],
'opt': {
'sender_name': 'SHEEPNET',
}}

system = {
'req': [],
'opt': {
'batt_voltage_overvoltage': 15.9,
'batt_voltage_normal': 12.6,
'batt_voltage_low': 11.8,
'batt_voltage_very_low': 11.5,
'batt_voltage_critical': 11.3,
'batt_warning_interval': 900,
'load_warning_interval': 900,
}}

weather = {
'req': ['api_key'],
'opt': {
'units': 'auto',
'language': 'en',
}}

config_structure = {
'megaio' : megaio,
'relay': { 1: relay, 2: relay, 3: relay, 4: relay, 5: relay, 6: relay, 7: relay, 8: relay },
'field': field,
'bme': bme,
'mppt': mppt,
'bmv': bmv,
'huawei': huawei,
'river': river,
'clickatell': clickatell,
'system': system,
'weather': weather,
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
        for config_block_name in loaded_yaml:

            config[config_block_name] = {}
            logger.info('Loading '+config_block_name+' config')

            # Relays are special because they have moar levels
            if config_block_name == 'relay':
            # For each relay
                for relay_id in config_structure['relay']:
                    try:
                        # If it's enabled in the config, load the data
                        if loaded_yaml['relay'][relay_id]['enabled']:
                            config['relay'][relay_id] = load_config_block('relay',relay,loaded_yaml['relay'][relay_id])
                        # Otherwise mark as disabled
                        else:
                            config['relay'][relay_id] = {}
                            config['relay'][relay_id]['enabled'] = False
                    # If we have missing keys, it's probably because the yaml is incomplete!
                    except KeyError:
                        logger.error('Relay '+str(relay_id)+' not properly configured!')
                        pass

            # All the other config blocks can be loaded in the same way
            elif config_block_name in config_structure:
                config[config_block_name] = load_config_block(config_block_name,config_structure[config_block_name],loaded_yaml[config_block_name])

            else:
                logger.warning('Unrecognised config block '+config_block_name+' not loaded!')

        # Check if things are missing and warn if they are
        for config_block in config_structure:
            if config_block not in config:
                logger.warning('Config block '+config_block+' missing from '+config_file)

        # This will disappear once other parts are rewritten
        # to use the config options rather than global_vars
        # hence why it is is separate to the above

        # If we get here we have successfully loaded the config!
        config['loaded'] = True

#    except Exception as e:
#        logger.error('Unhandled exception whilst loading config: ' + str(e))

    pass

def load_config_block(config_name, config_params, config_block):
    loaded_config_block = {}

    for attr in config_params['req']:
        if config_block.get(attr):
            loaded_config_block[attr] = config_block[attr]
        else:
            raise KeyError('Missing required configuration parameter in '+config_name+' config: '+attr)

    # Optional attributes
    for attr in config_params['opt']:
        # If they exist populate the data
        if config_block.get(attr):
            loaded_config_block[attr] = config_block[attr]
        # If not, populate the default
        else:
            loaded_config_block[attr] = config_params['opt'][attr]

    # Check for options that aren't expected
    for attr in config_block:
        if ( not attr in config_params['req']) and ( not attr in config_params['opt']):
            logger.warning('Unexpected option in '+config_name+' config: '+attr)

    return loaded_config_block
