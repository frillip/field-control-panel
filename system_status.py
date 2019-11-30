import time
import global_vars
import logging
import colorlog
import user_data
from datetime import datetime
from sms_sender import send_sms

handler = colorlog.StreamHandler()
handler.setFormatter(global_vars.log_format)
logger = colorlog.getLogger(__name__)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# This needs to be rewritten to use new BMV data

batt_voltage_overvoltage = 15.9
batt_voltage_normal = 12.8
batt_voltage_low = 11.8
batt_voltage_very_low = 11.5
batt_voltage_critical = 11.3
batt_voltage_sent = 0.0
batt_warning_sent = False
batt_warning_sent_time = 0
batt_warning_stage = 0
batt_warning_stage_text = {
-1: 'Overvoltage',
0: 'Normal',
1: 'Low',
2: 'Very low',
3: 'Critical',
4: 'Disconnected'
}
batt_warning_interval = 900
batt_state = True
batt_state_sent_time = 0

def check_batt_voltage():
    global batt_warning_stage
    global batt_warning_sent
    global batt_warning_sent_time
    global batt_voltage_sent
    global batt_state
    global batt_state_sent_time

    last_batt_warning_stage = batt_warning_stage
    human_datetime = datetime.now().strftime("%d/%m/%Y %H:%M")
    now_iso_stamp = datetime.now().replace(microsecond=0).isoformat()
    unix_time_int = int(time.time())
    warn_sms_text = ""
    last_batt_state = batt_state

    try:
        # First, a plausibility check...
        if global_vars.mppt_data["batt"]["v"] > 1.0 :
            batt_state = True
            # Is the battery charging or discharging?
            if global_vars.mppt_data["batt"]["cs"] == 0:
                # cs = 0 means the battery is not being charged
                if global_vars.mppt_data["batt"]["v"] < batt_voltage_critical:
                    new_batt_warning_stage = 3
                elif global_vars.mppt_data["batt"]["v"] < batt_voltage_very_low:
                    new_batt_warning_stage = 2
                elif global_vars.mppt_data["batt"]["v"] < batt_voltage_low:
                    new_batt_warning_stage = 1
                else:
                    new_batt_warning_stage = 0

                # Battery warning states should 'latch' upwards when discharging
                if new_batt_warning_stage > last_batt_warning_stage:
                    batt_warning_stage = new_batt_warning_stage

            else:
                if global_vars.mppt_data["batt"]["v"] > batt_voltage_overvoltage:
                    new_batt_warning_stage = -1
                elif global_vars.mppt_data["batt"]["v"] > batt_voltage_normal:
                    new_batt_warning_stage = 0
                elif global_vars.mppt_data["batt"]["v"] > batt_voltage_low:
                    new_batt_warning_stage = 1
                elif global_vars.mppt_data["batt"]["v"] > batt_voltage_very_low:
                    new_batt_warning_stage = 2
                else:
                    new_batt_warning_stage = 3

                # Latch downwards when charging, or battery returns to normal
                if new_batt_warning_stage < last_batt_warning_stage or new_batt_warning_stage == 0:
                    batt_warning_stage = new_batt_warning_stage

            if batt_warning_stage > last_batt_warning_stage and batt_warning_stage > 0:
                if batt_warning_stage == 1:
                    warn_sms_text = human_datetime + ": Battery voltage low! "+str(global_vars.mppt_data["batt"]["v"])+"V"
                    logger.warning("Battery voltage low! Current voltage: " + str(global_vars.mppt_data["batt"]["v"]) + "V. Sending alert SMS")
                elif batt_warning_stage == 2:
                    warn_sms_text = human_datetime + ": Battery voltage very low! "+str(global_vars.mppt_data["batt"]["v"])+"V"
                    logger.warning("Battery voltage very low! Current voltage: " + str(global_vars.mppt_data["batt"]["v"]) + "V. Sending alert SMS")
                elif batt_warning_stage == 3:
                    warn_sms_text = human_datetime + ": Battery voltage CRITICAL! "+str(global_vars.mppt_data["batt"]["v"])+"V"
                    logger.critical("Battery voltage critical! Current voltage: " + str(global_vars.mppt_data["batt"]["v"]) + "V. Sending alert SMS")
            elif batt_warning_stage < last_batt_warning_stage and batt_warning_stage > 0:
                warn_sms_text = human_datetime + ": Battery recharging: " + str(global_vars.mppt_data["batt"]["v"]) + "V"
                logger.info("Battery recharging: " + str(global_vars.mppt_data["batt"]["v"]) + "V. Sending notification SMS")
            elif ( batt_warning_stage != last_batt_warning_stage ) and batt_warning_stage == 0:
                warn_sms_text = human_datetime + ": Battery voltage returning to normal: " + str(global_vars.mppt_data["batt"]["v"]) + "V"
                logger.info("Battery voltage returning to normal: " + str(global_vars.mppt_data["batt"]["v"]) + "V. Sending notification SMS")
            elif ( batt_warning_stage != last_batt_warning_stage ) and batt_warning_stage == -1:
                warn_sms_text = human_datetime + ": Battery in overvoltage condition! Current voltage: " + str(global_vars.mppt_data["batt"]["v"]) + "V"
                logger.warning("Battery in overvoltage condition! Current voltage: " + str(global_vars.mppt_data["batt"]["v"]) + "V. Sending alert SMS")

            if (warn_sms_text and ( unix_time_int > batt_warning_sent_time + batt_warning_interval )) or (warn_sms_text and batt_warning_stage == 0):
                if ( batt_voltage_sent - 0.1 < global_vars.mppt_data["batt"]["v"] ) or ( batt_voltage_sent + 0.1 > global_vars.mppt_data["batt"]["v"] ) or batt_warning_stage == 0:
                    batt_voltage_sent = global_vars.mppt_data["batt"]["v"]
                    batt_warning_sent_time = unix_time_int
                    send_sms(user_data.voltage_warn_sms_list, warn_sms_text)
            global_vars.mppt_data["batt"]["state"] = batt_warning_stage
            global_vars.mppt_data["batt"]["state_text"] = batt_warning_stage_text[batt_warning_stage]

# Battery disconnected?
        else:
            batt_state = False

            if not batt_state and ( unix_time_int > batt_state_sent_time + batt_warning_interval ):
                warn_sms_text = human_datetime + ": Battery disconnected! Battery voltage: " + str(global_vars.mppt_data["batt"]["v"]) + "V"
                logger.critical("Battery disconnected! Battery voltage: " + str(global_vars.mppt_data["batt"]["v"]) + "V. Sending alert SMS")

            global_vars.mppt_data["batt"]["state"] = 4
            global_vars.mppt_data["batt"]["state_text"] = batt_warning_stage_text[batt_warning_stage]

        if batt_state != last_batt_state or ( warn_sms_text and not batt_state ):
            if batt_state:
                warn_sms_text = human_datetime + ": Battery now reconnected. Battery voltage: " + str(global_vars.mppt_data["batt"]["v"]) + "V"
                logger.warning("Battery now reconnected. Battery voltage: " + str(global_vars.mppt_data["batt"]["v"]) + "V. Sending alert SMS")
            else:
                warn_sms_text = human_datetime + ": Battery disconnected! Battery voltage: " + str(global_vars.mppt_data["batt"]["v"]) + "V"
                logger.critical("Battery disconnected! Battery voltage: " + str(global_vars.mppt_data["batt"]["v"]) + "V. Sending alert SMS")
            batt_state_sent_time = unix_time_int
            send_sms(user_data.voltage_warn_sms_list, warn_sms_text)

        pass

    except Exception as e:
        logger.error("MPPT battery voltage check failed: " + str(e))
        pass

last_load_state = True
last_load_state_time = 0
load_warning_interval = 900


# If the load is off warn, will only be triggered if Pi is moved onto a UPS of course...
def check_load_state():
    global last_load_state
    global last_load_state_time

    try:
        human_datetime = datetime.now().strftime("%d/%m/%Y %H:%M")
        now_iso_stamp = datetime.now().replace(microsecond=0).isoformat()
        unix_time_int = int(time.time())
        warn_sms_text = ""
        if global_vars.mppt_data["load"]["state"] != last_load_state:
            if global_vars.mppt_data["load"]["state"]:
                warn_sms_text = human_datetime + ": Load now reconnected. Battery voltage: " + str(global_vars.mppt_data["batt"]["v"]) + "V"
                logger.warning("Load now reconnected. Battery voltage: " + str(global_vars.mppt_data["batt"]["v"]) + "V. Sending alert SMS")
            else:
                warn_sms_text = human_datetime + ": Load disconnected! Battery voltage: " + str(global_vars.mppt_data["batt"]["v"]) + "V"
                logger.critical("Load disconnected! Battery voltage: " + str(global_vars.mppt_data["batt"]["v"]) + "V. Sending alert SMS")
            load_state_sent_time = unix_time_int
            send_sms(user_data.voltage_warn_sms_list, warn_sms_text)

        if not global_vars.mppt_data["load"]["state"] and ( unix_time_int > last_load_state_time + load_warning_interval ):
            warn_sms_text = human_datetime + ": Load disconnected! Battery voltage: " + str(global_vars.mppt_data["batt"]["v"]) + "V"
            logger.critical("Load disconnected! Battery voltage: " + str(global_vars.mppt_data["batt"]["v"]) + "V. Sending alert SMS")
            load_state_sent_time = unix_time_int
            send_sms(user_data.voltage_warn_sms_list, warn_sms_text)

        last_load_state = global_vars.mppt_data["load"]["state"]
        pass

    except Exception as e:
        logger.error("MPPT load state check failed: " + str(e))
        pass
