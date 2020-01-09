import yaml
from os import path
import global_vars
from megaio_set_relays import set_relay_state
import logging
import colorlog

handler = colorlog.StreamHandler()
handler.setFormatter(global_vars.log_format)
logger = colorlog.getLogger(__name__)
logger.addHandler(handler)
logger.setLevel(global_vars.log_level)

# Filename for save state file
save_state_file = 'save_state.yaml'

# Is the last state loaded (or has been attempted to be loaded)?
last_state_loaded= False

# What we are expecting to save / load
relay_save_list = ['last_state_change','state']
# Do we want relay state saving? Maybe, doesn't currently do anything and gets clobbered next time relays are read...
river_save_list = ['last_high','last_high_level','last_high_warn','last_level','last_timestamp','last_warn','last_warn_level','warning_active','status']

def save_running_state():
    try:
        logger.info("Saving current state")
        # Create the save state dict
        save_data = {}
        # Create the relay dict
        save_data['relay'] = {}
        logger.info("Saving relay data")
        for relay_id in global_vars.relay_data:
            # Create a dict for each individual relay
            save_data['relay'][relay_id] = {}

            # Not used but might be useful for interrogation
            save_data['relay'][relay_id]['enabled'] = global_vars.relay_data[relay_id]['enabled']

            # Save the attributes if the relay is enabled
            if global_vars.relay_data[relay_id]['enabled']:
                logger.info("Relay "+str(relay_id)+" enabled, saving")
                for attr in relay_save_list:
                    save_data['relay'][relay_id][attr] = global_vars.relay_data[relay_id][attr]
                # Save the auto timeout timestamp too
                save_data['relay'][relay_id]['state_change_timestamp'] = global_vars.relay_timestamp[relay_id]
            else:
                logger.info("Relay "+str(relay_id)+" disabled, skipping")

        # Do the same for the river data
        save_data['river'] = {}
        logger.info("Saving river data")
        for attr in river_save_list:
           save_data['river'][attr]=global_vars.river_data[attr]

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
        for save_block in last_saved_state:
            # For relays
            if save_block == 'relay':
                logger.info("Restoring relay data")
                # Iterate over each relay
                for relay_id in last_saved_state['relay']:
                    # Check the relay exists
                    if global_vars.relay_data.get(relay_id):
                        # Configuration is master for relay enabled, so no check here against last_saved_state['relay'][relay_id]['enabled']
                        if global_vars.relay_data[relay_id]['enabled']:
                            logger.info("Relay "+str(relay_id)+" enabled, restoring data")
                            # Iterate over the attributes in the yaml file
                            for attr in last_saved_state['relay'][relay_id]:
                                # Check if they exist in the list of things that we're expecting
                                if attr in relay_save_list:
                                     global_vars.relay_data[relay_id][attr] = last_saved_state['relay'][relay_id][attr]
                                # Or if they're the special auto timeout timestamp
                                elif attr == 'state_change_timestamp':
                                    global_vars.relay_timestamp[relay_id] = last_saved_state['relay'][relay_id]['state_change_timestamp']
                                # We ignore the 'enabled' option as config is master, and ignore (but warn) if there is unrecognised data
                                elif attr != 'enabled':
                                    logger.warning("Unrecognised save option in relay save state data: " + str(attr))
                            # Assert the saved relay state
                            set_relay_state(relay_id,global_vars.relay_data[relay_id]['state'])
                        else:
                            logger.info("Relay "+str(relay_id)+" disabled, skipping")
                    else:
                        logger.warning("Unkown relay in save state file: "+str(relay_id))

            # For river data
            elif save_block == 'river':
                logger.info("Restoring river data")
                # iterate over the attributes
                for attr in last_saved_state['river']:
                    # Restore them if they're expected
                    if attr in river_save_list:
                        global_vars.river_data[attr] = last_saved_state['river'][attr]
                    # Warn if they are not
                    else:
                        logger.warning("Unrecognised save option in relay save state data: " + str(attr))

        last_state_loaded = True

    except Exception as e:
        logger.error("Unhandled exception whilst loading last saved state: " + str(e))

    pass
