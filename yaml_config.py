import yaml
from os import path
import sys
import global_vars
import logging
import colorlog

logger = colorlog.getLogger(__name__)
logger.addHandler(global_vars.file_handler)
logger.addHandler(global_vars.handler)
logger.setLevel(global_vars.log_level)

# Which file is the config file?
config_file = 'config.yaml'

# Initialise the config dict
config = {}

# Useful config loaded var
config_loaded = False

# Define what is required, and what is optional (as well as default value if it is missing)
megaio = {
'req': [],
'opt': {
'stack_id': 0
},
'enum': {
}}

relay = {
'req': ['enabled', 'name'],
'opt': {
'invert': False,
'auto_off': 0,
'auto_on': 0,
'reminder_on': 0,
'reminder_on_sms_text': '',
'reminder_off': 0,
'reminder_off_sms_text': '',
'reminder_sms_list': [],
},
'enum': {
}}

field = {
'req': ['latitude', 'longitude'],
'opt': {
'elevation': 0,
'timezone': 'Europe/London',
},
'enum': {
}}

sensors = {
'req': [],
'opt': {
'i2c_port': 1,
'bme280_enable': False,
'bme280_address': 0x76, # Most sensors are 0x76, Adafruit is 0x77
'tsl2561_enable': False,
'tsl2561_address': 0x39, # Default address is 0x39 if address line is left floating
'tsl2561_gain': '1x',
'tsl2561_integration_time': '13ms',
'tsl2561_warn_enable': False,
'tsl2561_sms_list': [],
'lis3dh_enable': False,
'lis3dh_address': 0x19, #  Default address is 0x19
'lis3dh_interrupt_pin': None,
'lis3dh_warn_enable': False,
'lis3dh_sms_list': [],
'gps_enable': False,
},
'enum': { 'tsl2561_gain': { '1x':0, '16x':0 }, 'tsl2561_integration_time': { '13ms': 0x00, '101ms':0x01, '402ms':0x02},
}}

mppt = {
'req': ['tty_dev'],
'opt': {
'baudrate': 19200, # Default VE.Direct speed
},
'enum': {
}}

bmv = {
'req': ['tty_dev'],
'opt': {
'baudrate': 19200, # Default VE.Direct speed
'midpoint_enable': False,
'temp_enable': False,
'warn_enable': False,
'warn_sms_list': [],
},
'enum': {
}}

huawei = {
'req': ['dongle_ip'],
'opt': {
},
'enum': {
}}

river = {
'req': ['api_url', 'api_station_url'],
'opt': {
'high': 10.0,
'high_warn': 10.0,
'warn_enable': False,
'warn_sms_list': [],
},
'enum': {
}}

clickatell = {
'req': ['api_key'],
'opt': {
'sender_name': 'SHEEPNET',
},
'enum': {
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
},
'enum': {
}}

remote = {
'req': [],
'opt': {
'hostname': 'sheepnet',
'base_url': 'https://sheep.frillip.net/panel/',
'canary_url': 'canary',
'canary_string': 'Serinus canarius domesticus',
'interval': 15,
'timeout': 60,
'basic_user': '',
'basic_pass': '',
'warn_enable': False,
'warn_sms_list': [],
},
'enum': {
}}

weather = {
'req': ['api_key'],
'opt': {
'units': 'auto',
'language': 'en',
},
'enum': {
}}

picoups = {
'req': ['i2c_port'],
'opt': {
'battery_type': 'li-ion',
'to92_enable': False,
'fan_enable': False,
'fan_threshold_temp': 35,
},
'enum': {
'battery_type': {'li-ion': 0x49, 'lipo': 0x53, 'lifepo4':0x46},
}}

config_structure = {
'megaio' : megaio,
'relay': { 1: relay, 2: relay, 3: relay, 4: relay, 5: relay, 6: relay, 7: relay, 8: relay },
'field': field,
'sensors': sensors,
'mppt': mppt,
'bmv': bmv,
'huawei': huawei,
'river': river,
'clickatell': clickatell,
'system': system,
'remote': remote,
'weather': weather,
'picoups': picoups,
}

def load_config():
    global config
    global config_loaded

    try:
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
        config_loaded = True

    except Exception as e:
        logger.error('Unhandled exception whilst loading config: ' + str(e))
        sys.exit(1)


def load_config_block(config_name, config_params, config_block):
    loaded_config_block = {}

    # required attributes
    for attr in config_params['req']:
        # Make sure it exists before blindly trying to load it
        if config_block.get(attr):
            # Is it enumerated?
            if attr in config_params['enum']:
                # If it's enumerated correctly, load it
                if config_block[attr] in config_params['enum'][attr]:
                    loaded_config_block[attr] = config_params['enum'][attr][config_block[attr]]
                # If not, raise an exception
                else:
                    raise Exception('Required enumerated configuration parameter in '+config_name+' is not  valid value: ' +attr)
            # If not enumerated, just load it
            else:
                loaded_config_block[attr] = config_block[attr]
        # If missing, raise an exception
        else:
            raise KeyError('Missing required configuration parameter in '+config_name+' config: '+attr)

    # Optional attributes
    for attr in config_params['opt']:
        # If they exist populate the data
        if config_block.get(attr):
            # Is it enumerated?
            if attr in config_params['enum']:
                # If enumerated correctly, load it
                if config_block[attr] in config_params['enum'][attr]:
                    loaded_config_block[attr] = config_params['enum'][attr][config_block[attr]]
                # If not, populate the default, and warn
                else:
                    logger.warn('Unknown enumeration for '+config_name+' parameter: '+attr+'  Loading default instead')
                    loaded_config_block[attr] = config_params['opt'][attr]
            # If not enumerated, load it
            else:
                loaded_config_block[attr] = config_block[attr]
        # If not, populate the default
        else:
            loaded_config_block[attr] = config_params['opt'][attr]

    # Check for options that aren't expected, warn if found
    for attr in config_block:
        if ( not attr in config_params['req']) and ( not attr in config_params['opt']):
            logger.warning('Unexpected option in '+config_name+' config: '+attr)

    return loaded_config_block
