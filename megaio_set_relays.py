import megaio
from datetime import datetime
import global_vars
import logging

megaio_stack_id = 0

def set_relay_state(request):

    global megaio_stack_id
    logger = logging.getLogger("set relay state")
    now_iso_stamp = datetime.now().replace(microsecond=0).isoformat()
    try:
        for relay in request:
            if relay in global_vars.relay_map:
                relay_id = global_vars.relay_map[relay]

                if request[relay] == "on":
                    logger.warning("Manual " + relay + " on")
                    new_raw_state = True ^ global_vars.relay_data[relay_id]['invert']
                    megaio.set_relay(megaio_stack_id,relay_id,new_raw_state)
                    global_vars.relay_data[relay_id]['last_state_change'] = now_iso_stamp
                    global_vars.relay_timeout[relay_id] = global_vars.relay_data[relay_id]['auto_timeout']
                    return relay+" now ON"

                elif request[relay] == "off":
                    logger.warning("Manual " + relay + " off")
                    new_raw_state = False ^ global_vars.relay_data[relay_id]['invert']
                    megaio.set_relay(megaio_stack_id,relay_id,new_raw_state)
                    global_vars.relay_data[relay_id]['last_state_change'] = now_iso_stamp
                    global_vars.relay_timeout[relay_id] = global_vars.relay_data[relay_id]['auto_timeout']
                    return relay+" now OFF"

    except Exception as e:
        logger.error("Failed to set relay state: " + str(e))
        return "Something went wrong! Check the log... and the velociraptor paddock..."

    return "Ah-ah-ah! You didn't say the magic word!"

def relay_auto_timeout():

    global megaio_stack_id
    logger = logging.getLogger("relay auto timeout task")
    now_iso_stamp = datetime.now().replace(microsecond=0).isoformat()

    global_vars.relay_data.pop("e", None)
    for relay_id in global_vars.relay_data:
        try:
            if global_vars.relay_timeout[relay_id]:
                global_vars.relay_timeout[relay_id] -= 1

            if global_vars.relay_data[relay_id]['auto_timeout'] and not global_vars.relay_timeout[relay_id]:

# Turn off a relay if it is on and the timout has expired
                if global_vars.relay_data[relay_id]['auto_off'] and global_vars.relay_data[relay_id]['state']:
                    logger.warning("Auto " + global_vars.relay_data[relay_id]['name'] + " off")
                    new_raw_state = False ^ global_vars.relay_data[relay_id]['invert']
                    megaio.set_relay(megaio_stack_id,relay_id,new_raw_state)
                    global_vars.relay_data[relay_id]['last_state_change'] = now_iso_stamp

# Turn on a relay if it is off and the timout has expired
                if global_vars.relay_data[relay_id]['auto_on'] and not global_vars.relay_data[relay_id]['state']:
                    logger.waning(": Auto " + global_vars.relay_data[relay_id]['name'] + " on")
                    new_raw_state = True ^ global_vars.relay_data[relay_id]['invert']
                    megaio.set_relay(megaio_stack_id,relay_id,new_raw_state)
                    global_vars.relay_data[relay_id]['last_state_change'] = now_iso_stamp

        except Exception as e:
            logger.error("Failed to auto switch " + global_vars.relay_data[relay_id]['name'] + "relay: " + str(e))
            global_vars.relay_timeout[relay_id] = 0

    global_vars.relay_data["e"] = False

    pass
