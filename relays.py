import megaio
from datetime import datetime
import time
import global_vars
from yaml_config import config
from sms_sender import send_sms
import logging
import colorlog

logger = colorlog.getLogger(__name__)
logger.addHandler(global_vars.file_handler)
logger.addHandler(global_vars.handler)
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

relay_map = {}
relay_state = {}

# Function that gets ALL the relay states
def get_relay_data():

    try:
        # For some reason, you can only read ALL of the relay states as a single byte, so do this
        relay_byte=megaio.get_relays(config['megaio']['stack_id'])
        # Then for each relay
        for relay_id in config['relay']:
            # And if it's enabled
            if config['relay'][relay_id]['enabled']:
                # Bitmask it to get the raw state
                relay_state[relay_id]['raw_state'] = bool(relay_byte & relay_mask[relay_id])
                # And invert to get the 'true' state if required
                relay_state[relay_id]['state'] = relay_state[relay_id]['raw_state'] ^ config['relay'][relay_id]['invert']

    except Exception as e:
        # Error has occurred, log it
        logger.error("Relay data task failed: " + str(e))


def relay_handle_request(request):
    try:
        # Theoretically we can switch multiple relays in one request, so handle them individually
        for relay in request:
            # Check if the relay name is in the relay map
            if relay in relay_map:
                # Get the corresponding relay_id
                relay_id = relay_map[relay]
                # If it's a request to turn it on, do so, and return some text saying so
                if request[relay] == "on":
                    set_relay_state(relay_id,True)
                    logger.warning("Manual " + relay + " on")
                    return relay+" now ON"

                elif request[relay] == "off":
                    # If it's a request to turn it off, do so, and return some text saying so
                    set_relay_state(relay_id,False)
                    logger.warning("Manual " + relay + " off")
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
    human_datetime = datetime.now().strftime("%d/%m/%Y %H:%M")
    # For every relay in the timestamp dict
    for relay_id in relay_state:
        try:
            # If auto_off is set and the relay is on
            if config['relay'][relay_id]['auto_off'] and relay_state[relay_id]['state']:
                # Check if the timeout has expired
                if ( unix_time_int >= relay_state[relay_id]['state_change_timestamp'] + config['relay'][relay_id]['auto_off'] ):
                    logger.warning("Auto " + config['relay'][relay_id]['name'] + " off")
                    # If we've reminded via SMS, warn via SMS AFTER we change the relay
                    if relay_state[relay_id]['reminder_sent'] and config['relay'][relay_id]['reminder_on'] and not relay_state[relay_id]['auto_off_sent']:
                        set_relay_state(relay_id,False)
                        sms_text = human_datetime + ": " + config['relay'][relay_id]['name'].capitalize() + ' has now been automatically turned off'
                        send_sms(config['relay'][relay_id]['reminder_sms_list'],sms_text)
                        relay_state[relay_id]['auto_off_sent'] = True
                    # Otherwise, just change the state of the relay
                    else:
                        set_relay_state(relay_id,False)

            # If auto_on is set and the relay is off
            if config['relay'][relay_id]['auto_on'] and not relay_state[relay_id]['state']:
                # If check if the timeout has expired
                if ( unix_time_int >= relay_state[relay_id]['state_change_timestamp'] + config['relay'][relay_id]['auto_on'] ):
                    logger.warning(": Auto " + config['relay'][relay_id]['name'] + " on")
                    # If we've reminded via SMS, warn via SMS AFTER we change the relay
                    if relay_state[relay_id]['reminder_sent'] and config['relay'][relay_id]['reminder_off'] and not relay_state[relay_id]['auto_on_sent']:
                        set_relay_state(relay_id,True)
                        sms_text = human_datetime + ": " + config['relay'][relay_id]['name'].capitalize() + ' has now been automatically turned on'
                        send_sms(config['relay'][relay_id]['reminder_sms_list'],sms_text)
                        relay_state[relay_id]['auto_on_sent'] = True
                    # Otherwise, just change the state of the relay
                    else:
                        set_relay_state(relay_id,True)

        except Exception as e:
            # Log an error if one has occurred
            logger.error("Failed to auto switch " + config['relay'][relay_id]['name'] + " relay: " + str(e))


def relay_reminder_timeout():
    # Get current ISO timestamp for JSON and unix timestamp for timeout
    human_datetime = datetime.now().strftime("%d/%m/%Y %H:%M")
    unix_time_int = int(time.time())
    now_iso_stamp = datetime.now().replace(microsecond=0).isoformat()
    # For every relay in the timestamp dict
    for relay_id in relay_state:
        try:
            # If reminder_on is set and the relay is on
            if config['relay'][relay_id]['reminder_on'] and relay_state[relay_id]['state']:
                # Check if we've already sent a reminder
                if not relay_state[relay_id]['reminder_active']:
                    # Check if the timeout has expired
                    if ( unix_time_int >= relay_state[relay_id]['state_change_timestamp'] + config['relay'][relay_id]['reminder_on'] ):
                        logger.warning("Sending SMS reminder to turn " + config['relay'][relay_id]['name'] + " off")
                        sms_text = human_datetime + ": " + config['relay'][relay_id]['reminder_on_sms_text']
                        send_sms(config['relay'][relay_id]['reminder_sms_list'],sms_text)
                        relay_state[relay_id]['reminder_sent'] = True
                        relay_state[relay_id]['reminder_time'] = now_iso_stamp

            # If reminder_off is set and the relay is off
            if config['relay'][relay_id]['reminder_off'] and not relay_state[relay_id]['state']:
                # Check if we've already sent a reminder
                if not relay_state[relay_id]['reminder_sent']:
                    # Check if the timeout has expired
                    if ( unix_time_int >= relay_state[relay_id]['state_change_timestamp'] + config['relay'][relay_id]['reminder_off'] ):
                        logger.warning("Sending SMS reminder to turn " + config['relay'][relay_id]['name'] + " on")
                        sms_text = human_datetime + ": " + config['relay'][relay_id]['reminder_off_sms_text']
                        send_sms(config['relay'][relay_id]['reminder_sms_list'],sms_text)
                        relay_state[relay_id]['reminder_sent'] = True
                        relay_state[relay_id]['reminder_time'] = now_iso_stamp

        except Exception as e:
            # Log an error if one has occurred
            logger.error("Failed to check reminder status for " + config['relay'][relay_id]['name'] + "relay: " + str(e))


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
        relay_state[relay_id]['state'] = new_state
        relay_state[relay_id]['raw_state'] = new_raw_state
        relay_state[relay_id]['last_state_change'] = now_iso_stamp
        relay_state[relay_id]['state_change_timestamp'] = unix_time_int
        relay_state[relay_id]['reminder_sent'] = False
        relay_state[relay_id]['auto_off_sent'] = False
        relay_state[relay_id]['auto_on_sent'] = False
        if new_state:
            logger.warning(config['relay'][relay_id]['name']+' now on')
        else:
            logger.warning(config['relay'][relay_id]['name']+' now off')

    except Exception as e:
        # Log an error if one has occurred
        logger.error("Error setting relay state: " + str(e))


def generate_relay_map():
    try:
        logger.info('Generating relay mappings')
        for relay_id in config['relay']:
            if config['relay'][relay_id]['enabled']:
                relay_name = config['relay'][relay_id]['name']
                relay_map[relay_name] = relay_id
                relay_state[relay_id] = {}

    except Exception as e:
        # Error has occurred, log it
        logger.error('Failed to generate relay mapping: ' + str(e))


def generate_relay_reminders():
    try:
        logger.info('Generating relay SMS reminders as necessary')
        for relay_id in config['relay']:
            if config['relay'][relay_id]['enabled']:
                if config['relay'][relay_id]['reminder_on'] and not config['relay'][relay_id]['reminder_on_sms_text']:
                    config['relay'][relay_id]['reminder_on_sms_text'] = config['relay'][relay_id]['name'].capitalize() + " has been left on."
                    logger.warning("No reminder on SMS text for relay " + str(relay_id) + ", using: " + config['relay'][relay_id]['reminder_on_sms_text'])
                if config['relay'][relay_id]['reminder_off'] and not config['relay'][relay_id]['reminder_off_sms_text']:
                    config['relay'][relay_id]['reminder_off_sms_text'] = config['relay'][relay_id]['name'].capitalize() + " has been left off."
                    logger.warning("No reminder on SMS text for relay " + str(relay_id) + ", using: " + config['relay'][relay_id]['reminder_off_sms_text'])

    except Exception as e:
        # Error has occurred, log it
        logger.error('Failed to generate relay SMS reminders: ' + str(e))


def generate_relay_json():
    relay_data = config['relay']
    for relay_id in relay_data:
        if config['relay'][relay_id]['enabled']:
            for attr in relay_state[relay_id]:
                relay_data[relay_id][attr] = relay_state[relay_id][attr]
    return relay_data
