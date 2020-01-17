import yaml
from os import path
import global_vars
from yaml_config import config
from relays import get_relay_data,set_relay_state,relay_state
from environment_agency import river_data
from datetime import datetime
import time
import system_status
import logging
import colorlog

handler = colorlog.StreamHandler()
handler.setFormatter(global_vars.log_format)
logger = colorlog.getLogger(__name__)
logger.addHandler(handler)
logger.setLevel(global_vars.log_level)

now_iso_stamp = datetime.now().replace(microsecond=0).isoformat()
unix_time_int = int(time.time())

# Filename for save state file
save_state_file = 'save_state.yaml'

last_state_loaded = False

# What we are expecting to save / load
relay_save_list = {
'last_state_change': now_iso_stamp,
'state_change_timestamp': unix_time_int,
}

river_save_list = {
'last_high':  now_iso_stamp,
'last_high_level': 0.0,
'last_high_warn': 0.0,
'last_level': now_iso_stamp,
'last_timestamp': now_iso_stamp,
'last_warn': now_iso_stamp,
'last_warn_level': 0.0,
'warning_active': False,
'status': 'steady',
}

system_save_list = {
'batt_state': True,
'batt_state_sent_time': 0,
'last_load_state': True,
'last_load_state_time': 0,
'batt_voltage_sent': 0.0,
'batt_warning_sent': False,
'batt_warning_sent_time': 0,
'batt_warning_stage': 0,
}

save_state_structure = {
'relay': relay_save_list,
'river': river_save_list,
'system': system_save_list,
}

def save_running_state():
    try:
        logger.info("Saving current state")
        # Create the save state dict
        save_data = {}
        # Create the relay dict
        save_data['relay'] = {}
        logger.info("Saving relay data")
        for relay_id in config['relay']:
            # Create a dict for each individual relay
            save_data['relay'][relay_id] = {}

            # Not used but might be useful for interrogation
            save_data['relay'][relay_id]['enabled'] = config['relay'][relay_id]['enabled']

            # Save the attributes if the relay is enabled
            if config['relay'][relay_id]['enabled']:
                logger.info("Relay "+str(relay_id)+" enabled, saving")
                for attr in relay_save_list:
                    save_data['relay'][relay_id][attr] = relay_state[relay_id][attr]
            else:
                logger.info("Relay "+str(relay_id)+" disabled, skipping")

        # Do the same for the river data
        save_data['river'] = {}
        logger.info("Saving river data")
        for attr in river_save_list:
           if attr.startswith('last_'):
               last_attr = attr[5:]
               save_data['river'][attr]=river_data['last'][last_attr]
           else:
               save_data['river'][attr]=river_data[attr]

        # Do the same for the river data
        save_data['system'] = {}
        logger.info("Saving river data")
        for attr in system_save_list:
           save_data['system'][attr]=system_status.system_state[attr]

        # Write to yaml file
        logger.info("Writing to "+save_state_file)
        with open(save_state_file, 'w') as file:
            save_state = yaml.safe_dump(save_data, file)

    except Exception as e:
        logger.error("Unhandled exception whilst saving current state: " + str(e))

    logger.info("Current state successfully saved")

    pass


def load_last_saved_state():
    try:
        logger.info("Restoring last saved state")
        # Check if the file exists first
        if path.exists(save_state_file):
            # Open an load the yaml if it does
            with open(save_state_file, 'r') as file:
                logger.info("Opened "+save_state_file)
                last_saved_state = yaml.safe_load(file)
        else:
            # Warn if it doesn't
            logger.warning("No saved state file found!")
            pass

        # Iterate through the saved blocks of data
        for save_block in save_state_structure:
            # For relays
            if save_block == 'relay':
                logger.info("Restoring relay data")
                # Current relay state is remembered by megaio
                # board so get current relay state first
                logger.info("Getting current relay state")
                get_relay_data()
                if not last_saved_state.get('relay'):
                    logger.warning('Missing relay data block in save state')
                    last_saved_state['relay'] = {}
                # Iterate over each relay
                for relay_id in config['relay']:
                    # Check the relay exists
                    if not last_saved_state['relay'].get(relay_id):
                        logger.warning("No save data for relay "+str(relay_id))
                        last_saved_state['relay'][relay_id] = {}
                    # Configuration is master for relay enabled, so no check here against last_saved_state['relay'][relay_id]['enabled']
                    if config['relay'][relay_id]['enabled']:
                        logger.info("Relay "+str(relay_id)+" enabled, restoring data")
                        # Iterate over the attributes in the yaml file
                        for attr in relay_save_list:
                            # Check if they exist in the list of things that we're expecting
                            if attr in last_saved_state['relay'][relay_id]:
                                 relay_state[relay_id][attr] = last_saved_state['relay'][relay_id][attr]
                            # We ignore the 'enabled' option as config is master, and ignore (but warn) if there is unrecognised data
                            elif attr == 'enabled':
                                pass
                            else:
                                logger.warning('Missing data in relay save state, loading default: ' + str(attr)+' : '+str(relay_save_list[attr]))
                                relay_state[relay_id][attr] = relay_save_list[attr]
                    else:
                        logger.info("Relay "+str(relay_id)+" disabled, skipping")

            # For river data
            elif save_block == 'river':
                logger.info('Restoring river data')
                if not last_saved_state.get('river'):
                    logger.warning('Missing river data block in save state')
                    last_saved_state['river'] = {}
                # iterate over the attributes
                for attr in river_save_list:
                    # Restore them if they're expected
                    if attr in last_saved_state['river']:
                        if attr.startswith('last_'):
                            last_attr = attr[5:]
                            river_data['last'][last_attr] = last_saved_state['river'][attr]
                        else:
                            river_data[attr] = last_saved_state['river'][attr]
                    # Load default if not
                    else:
                        logger.warning('Missing data in river save state, loading default: ' + str(attr)+' : '+str(river_save_list[attr]))
                        if attr.startswith('last_'):
                            last_attr = attr[5:]
                            river_data['last'][last_attr] = river_save_list[attr]
                        else:
                            river_data['last'][attr] = river_save_list[attr]

            # For system data
            elif save_block == 'system':
                logger.info('Restoring system data')
                if not last_saved_state.get('system'):
                    last_saved_state['system'] = {}
                    logger.warning('Missing system data block in save state')
                # Iterate over the attributes
                for attr in system_save_list:
                    # Restore them if they're expected
                    if attr in last_saved_state['system']:
                        system_status.system_state[attr] = last_saved_state['system'][attr]
                    # Load default if not
                    else:
                        system_status.system_state[attr] = system_save_list[attr]
                        logger.warning('Missing data in system save state, loading default: ' + str(attr)+' : '+str(system_save_list[attr]))

        last_state_loaded = True

    except Exception as e:
        logger.error("Unhandled exception whilst loading last saved state: " + str(e))

    pass
