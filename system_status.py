import time
import global_vars
import logging
import colorlog
from yaml_config import config
from datetime import datetime
from sms_sender import send_sms

handler = colorlog.StreamHandler()
handler.setFormatter(global_vars.log_format)
logger = colorlog.getLogger(__name__)
logger.addHandler(handler)
logger.setLevel(global_vars.log_level)

batt_warning_stage_text = {
-1: 'Overvoltage',
0: 'Normal',
1: 'Low',
2: 'Very low',
3: 'Critical',
4: 'Disconnected'
}


system_state = {}

# This needs to be rewritten to use new BMV data

def check_batt_voltage():

    last_batt_warning_stage = system_state['batt_warning_stage']
    human_datetime = datetime.now().strftime("%d/%m/%Y %H:%M")
    now_iso_stamp = datetime.now().replace(microsecond=0).isoformat()
    unix_time_int = int(time.time())
    warn_sms_text = ""
    last_batt_state = system_state['batt_state']

    try:
        # First, a plausibility check...
        if global_vars.mppt_data["batt"]["v"] > 1.0 :
            system_state['batt_state'] = True
            # Is the battery charging or discharging?
            if global_vars.mppt_data["batt"]["cs"] == 0:
                # cs = 0 means the battery is not being charged
                if global_vars.mppt_data["batt"]["v"] < config['system']['batt_voltage_critical']:
                    new_batt_warning_stage = 3
                elif global_vars.mppt_data["batt"]["v"] < config['system']['batt_voltage_very_low']:
                    new_batt_warning_stage = 2
                elif global_vars.mppt_data["batt"]["v"] < config['system']['batt_voltage_low']:
                    new_batt_warning_stage = 1
                else:
                    new_batt_warning_stage = 0

                # Battery warning states should 'latch' upwards when discharging
                if new_batt_warning_stage > last_batt_warning_stage:
                    system_state['batt_warning_stage'] = new_batt_warning_stage

            else:
                if global_vars.mppt_data["batt"]["v"] > config['system']['batt_voltage_overvoltage']:
                    new_batt_warning_stage = -1
                elif global_vars.mppt_data["batt"]["v"] > config['system']['batt_voltage_normal']:
                    new_batt_warning_stage = 0
                elif global_vars.mppt_data["batt"]["v"] > config['system']['batt_voltage_low']:
                    new_batt_warning_stage = 1
                elif global_vars.mppt_data["batt"]["v"] > config['system']['batt_voltage_very_low']:
                    new_batt_warning_stage = 2
                else:
                    new_batt_warning_stage = 3

                # Latch downwards when charging, or battery returns to normal
                if new_batt_warning_stage < last_batt_warning_stage or new_batt_warning_stage == 0:
                    system_state['batt_warning_stage'] = new_batt_warning_stage

            if system_state['batt_warning_stage'] > last_batt_warning_stage and system_state['batt_warning_stage'] > 0:
                if system_state['batt_warning_stage'] == 1:
                    warn_sms_text = human_datetime + ": Battery voltage low! "+str(global_vars.mppt_data["batt"]["v"])+"V"
                    logger.warning("Battery voltage low! Current voltage: " + str(global_vars.mppt_data["batt"]["v"]) + "V. Sending alert SMS")
                elif system_state['batt_warning_stage'] == 2:
                    warn_sms_text = human_datetime + ": Battery voltage very low! "+str(global_vars.mppt_data["batt"]["v"])+"V"
                    logger.warning("Battery voltage very low! Current voltage: " + str(global_vars.mppt_data["batt"]["v"]) + "V. Sending alert SMS")
                elif system_state['batt_warning_stage'] == 3:
                    warn_sms_text = human_datetime + ": Battery voltage CRITICAL! "+str(global_vars.mppt_data["batt"]["v"])+"V"
                    logger.critical("Battery voltage critical! Current voltage: " + str(global_vars.mppt_data["batt"]["v"]) + "V. Sending alert SMS")
            elif system_state['batt_warning_stage'] < last_batt_warning_stage and system_state['batt_warning_stage'] > 0:
                warn_sms_text = human_datetime + ": Battery recharging: " + str(global_vars.mppt_data["batt"]["v"]) + "V"
                logger.info("Battery recharging: " + str(global_vars.mppt_data["batt"]["v"]) + "V. Sending notification SMS")
            elif ( system_state['batt_warning_stage'] != last_batt_warning_stage ) and system_state['batt_warning_stage'] == 0:
                warn_sms_text = human_datetime + ": Battery voltage returning to normal: " + str(global_vars.mppt_data["batt"]["v"]) + "V"
                logger.info("Battery voltage returning to normal: " + str(global_vars.mppt_data["batt"]["v"]) + "V. Sending notification SMS")
            elif ( system_state['batt_warning_stage'] != last_batt_warning_stage ) and system_state['batt_warning_stage'] == -1:
                warn_sms_text = human_datetime + ": Battery in overvoltage condition! Current voltage: " + str(global_vars.mppt_data["batt"]["v"]) + "V"
                logger.warning("Battery in overvoltage condition! Current voltage: " + str(global_vars.mppt_data["batt"]["v"]) + "V. Sending alert SMS")

            if (warn_sms_text and ( unix_time_int > system_state['batt_warning_sent_time'] + config['system']['batt_warning_interval'] )) or (warn_sms_text and system_state['batt_warning_stage'] == 0):
                if ( system_state['batt_voltage_sent'] - 0.1 < global_vars.mppt_data["batt"]["v"] ) or ( system_state['batt_voltage_sent'] + 0.1 > global_vars.mppt_data["batt"]["v"] ) or system_state['batt_warning_stage'] == 0:
                    system_state['batt_voltage_sent'] = global_vars.mppt_data["batt"]["v"]
                    system_state['batt_warning_sent_time'] = unix_time_int
                    send_sms(config['bmv']['warn_sms_list'], warn_sms_text)
            global_vars.mppt_data["batt"]["state"] = system_state['batt_warning_stage']
            global_vars.mppt_data["batt"]["state_text"] = batt_warning_stage_text[system_state['batt_warning_stage']]

# Battery disconnected?
        else:
            system_state['batt_state'] = False

            if not system_state['batt_state'] and ( unix_time_int > system_state['batt_state_sent_time'] + config['system']['batt_warning_interval'] ):
                warn_sms_text = human_datetime + ": Battery disconnected! Battery voltage: " + str(global_vars.mppt_data["batt"]["v"]) + "V"
                logger.critical("Battery disconnected! Battery voltage: " + str(global_vars.mppt_data["batt"]["v"]) + "V. Sending alert SMS")

            global_vars.mppt_data["batt"]["state"] = 4
            global_vars.mppt_data["batt"]["state_text"] = batt_warning_stage_text[system_state['batt_warning_stage']]

        if system_state['batt_state'] != last_batt_state or ( warn_sms_text and not system_state['batt_state'] ):
            if system_state['batt_state']:
                warn_sms_text = human_datetime + ": Battery now reconnected. Battery voltage: " + str(global_vars.mppt_data["batt"]["v"]) + "V"
                logger.warning("Battery now reconnected. Battery voltage: " + str(global_vars.mppt_data["batt"]["v"]) + "V. Sending alert SMS")
            else:
                warn_sms_text = human_datetime + ": Battery disconnected! Battery voltage: " + str(global_vars.mppt_data["batt"]["v"]) + "V"
                logger.critical("Battery disconnected! Battery voltage: " + str(global_vars.mppt_data["batt"]["v"]) + "V. Sending alert SMS")
            system_state['batt_state_sent_time'] = unix_time_int
            send_sms(config['bmv']['warn_sms_list'], warn_sms_text)

        pass

    except Exception as e:
        logger.error("MPPT battery voltage check failed: " + str(e))
        pass

# If the load is off warn, will only be triggered if Pi is moved onto a UPS of course...
def check_load_state():

    try:
        human_datetime = datetime.now().strftime("%d/%m/%Y %H:%M")
        now_iso_stamp = datetime.now().replace(microsecond=0).isoformat()
        unix_time_int = int(time.time())
        warn_sms_text = ""
        if global_vars.mppt_data["load"]["state"] != system_state['last_load_state']:
            if global_vars.mppt_data["load"]["state"]:
                warn_sms_text = human_datetime + ": Load now reconnected. Battery voltage: " + str(global_vars.mppt_data["batt"]["v"]) + "V"
                logger.warning("Load now reconnected. Battery voltage: " + str(global_vars.mppt_data["batt"]["v"]) + "V. Sending alert SMS")
            else:
                warn_sms_text = human_datetime + ": Load disconnected! Battery voltage: " + str(global_vars.mppt_data["batt"]["v"]) + "V"
                logger.critical("Load disconnected! Battery voltage: " + str(global_vars.mppt_data["batt"]["v"]) + "V. Sending alert SMS")
            system_state['load_state_sent_time'] = unix_time_int
            send_sms(config['bmv']['warn_sms_list'], warn_sms_text)

        if not global_vars.mppt_data["load"]["state"] and ( unix_time_int > system_state['last_load_state_time'] + config['system']['load_warning_interval'] ):
            warn_sms_text = human_datetime + ": Load disconnected! Battery voltage: " + str(global_vars.mppt_data["batt"]["v"]) + "V"
            logger.critical("Load disconnected! Battery voltage: " + str(global_vars.mppt_data["batt"]["v"]) + "V. Sending alert SMS")
            system_state['load_state_sent_time'] = unix_time_int
            send_sms(config['bmv']['warn_sms_list'], warn_sms_text)

        system_state['last_load_state'] = global_vars.mppt_data["load"]["state"]
        pass

    except Exception as e:
        logger.error("MPPT load state check failed: " + str(e))
        pass
