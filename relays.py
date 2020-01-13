import megaio
from datetime import datetime
import time
import global_vars
from yaml_config import config
import logging
import colorlog

handler = colorlog.StreamHandler()
handler.setFormatter(global_vars.log_format)
logger = colorlog.getLogger(__name__)
logger.addHandler(handler)
logger.setLevel(global_vars.log_level)

# Bit mask dict for reading individual relays
relay_mask = { 1 : 0x01,
               2 : 0x02,
               3 : 0x04,
               4 : 0x08,
               5 : 0x10,
               6 : 0x20,
               7 : 0x40,
               8 : 0x80 }

# Function that gets ALL the relay states
def get_relay_data():

    try:
        # For some reason, you can only read ALL of the relay states as a single byte, so do this
        relay_byte=megaio.get_relays(config['megaio']['stack_id'])
        # Then for each relay
        for relay_id in global_vars.relay_data:
            # And if it's enabled
            if config['relay'][relay_id]['enabled']:
                # Bitmask it to get the raw state
                global_vars.relay_data[relay_id]['raw_state'] = bool(relay_byte & relay_mask[relay_id])
                # And invert to get the 'true' state if required
                global_vars.relay_data[relay_id]['state'] = global_vars.relay_data[relay_id]['raw_state'] ^ config['relay'][relay_id]['invert']

    except Exception as e:
        # Error has occurred, log it
        logger.error("Relay data task failed: " + str(e))


def relay_handle_request(request):
    try:
        # Theoretically we can switch multiple relays in one request, so handle them individually
        for relay in request:
            # Check if the relay name is in the relay map
            if relay in global_vars.relay_map:
                # Get the corresponding relay_id
                relay_id = global_vars.relay_map[relay]
                # If it's a request to turn it on, do so, and return some text saying so
                if request[relay] == "on":
                    logger.warning("Manual " + relay + " on")
                    set_relay_state(relay_id,True)
                    return relay+" now ON"

                elif request[relay] == "off":
                    # If it's a request to turn it off, do so, and return some text saying so
                    logger.warning("Manual " + relay + " off")
                    set_relay_state(relay_id,False)
                    return relay+" now OFF"
                else:
                    # If it's neither, log an error, and return some text saying so
                    logger.error("Garbled relay request, no valid state: "+str(request))
                    return "Ah-ah-ah! You didn't say the magic word!"
            else:
                # If it's a not a valid relay name, log an error, and return some text saying so
                logger.error("Garbled relay request, no valid relay: "+str(request))
                return "Ah-ah-ah! You didn't say the magic word!"

    except Exception as e:
        # Something else has gone wrong, log the error
        logger.error("Failed to set relay state: " + str(e))
        return "Something went wrong! Check the log... and the velociraptor paddock..."

    # And as a catch all, frustrate Samual L Jackson some more
    return "Ah-ah-ah! You didn't say the magic word!"


def relay_auto_timeout():
    # Get current unix timestamp
    unix_time_int = int(time.time())
    # For every relay in the timestamp dict
    for relay_id in global_vars.relay_timestamp:
        try:
            # Check if the timeout has expired
            if ( unix_time_int >= global_vars.relay_timestamp[relay_id] + config['relay'][relay_id]['auto_timeout'] ):

                # If auto_off is set, turn relay off if it is on
                if config['relay'][relay_id]['auto_off'] and global_vars.relay_data[relay_id]['state']:
                    logger.warning("Auto " + config['relay'][relay_id]['name'] + " off")
                    set_relay_state(relay_id,False)

                # If auto_on is set, turn relay on if it is off
                if config['relay'][relay_id]['auto_on'] and not global_vars.relay_data[relay_id]['state']:
                    logger.waning(": Auto " + config['relay'][relay_id]['name'] + " on")
                    set_relay_state(relay_id,True)

        except Exception as e:
            # Log an error if one has occurred
            logger.error("Failed to auto switch " + config['relay'][relay_id]['name'] + "relay: " + str(e))


def set_relay_state(relay_id, new_state):
    # Get current ISO timestamp for JSON and unix timestamp for timeout
    unix_time_int = int(time.time())
    now_iso_stamp = datetime.now().replace(microsecond=0).isoformat()

    try:
        # Make sure new_state is boolean
        new_state = bool(new_state)
        # XOR with the 'invert' attribute to get the new_raw_state
        new_raw_state = new_state ^ config['relay'][relay_id]['invert']
        # Set the relay via megaio library
        megaio.set_relay(config['megaio']['stack_id'],relay_id,new_raw_state)
        # Update the relay data immediately, rather than waiting for get_relay_data() to run
        global_vars.relay_data[relay_id]['state'] = new_state
        global_vars.relay_data[relay_id]['raw_state'] = new_raw_state
        global_vars.relay_data[relay_id]['last_state_change'] = now_iso_stamp
        global_vars.relay_timestamp[relay_id] = unix_time_int
        if new_state:
            logger.warning(config['relay'][relay_id]['name']+' now on')
        else:
            logger.warning(config['relay'][relay_id]['name']+' now off')

    except Exception as e:
        # Log an error if one has occurred
        logger.error("Error setting relay state: " + str(e))

