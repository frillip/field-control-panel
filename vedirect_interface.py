import time
import serial
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


mppt_tty_dev = '/dev/ttyUSB0'
baudrate = 19200

off_text = {
0x001: 'No input power',
0x002: 'Switched off (power switch)',
0x004: 'Switched off (register)',
0x008: 'Remote input',
0x010: 'Protection active',
0x020: 'Paygo',
0x040: 'BMS',
0x080: 'Engine shutdown detection',
0x100: 'Analysing input voltage'
}

cs_text = {
0: 'Not charging',
2: 'Fault',
3: 'Bulk',
4: 'Absorption',
5: 'Float',
7: 'Equalize (manual)',
245: 'Starting-up',
247: 'Auto equalize',
252: 'External control'
}

err_text = {
0: 'No error',
2: 'Battery voltage too high',
3: 'Remote temperature sensor failure',
4: 'Remote temperature sensor failure',
5: 'Remote temperature sensor failure (connection lost)',
6: 'Remote battery voltage sense failure',
7: 'Remote battery voltage sense failure',
8: 'Remote battery voltage sense failure (connection lost)',
17: 'Charger temperature too high',
18: 'Charger over current',
19: 'Charger current reversed',
20: 'Bulk time limit exceeded',
21: 'Current sensor issue (sensor bias/sensor broken)',
26: 'Terminals overheated',
28: 'Power stage issue',
33: 'Input voltage too high (solar panel)',
34: 'Input current too high (solar panel)',
38: 'Input shutdown (due to excessive battery voltage)',
39: 'Input shutdown',
65: 'Lost communication',
66: 'Charging configuartion issue',
67: 'BMS Connection lost',
68: 'Network misconfigured',
114: 'CPU temperature too high',
116: 'Factory calibration data lost',
117: 'Invalid/incompatible firmware',
119: 'User settings invalid'
}

mppt_text = {
0: 'Off',
1: 'Voltage or current limited',
2: 'MPP Tracker active'
}

def get_mppt_data():

    global tty_dev
    global baudrate
    global err_text
    global cs_text
    global mppt_text

    mppt_raw_data = {}

    try:
        ser = serial.Serial()
        ser.port = mppt_tty_dev
        ser.baudrate = baudrate
        ser.parity = serial.PARITY_NONE
        ser.stopbits = serial.STOPBITS_ONE
        ser.bytesize = serial.EIGHTBITS
        ser.timeout = 1

        ser.open()
        ser.flushInput()
        block_start = False
        while not block_start:
            ve_string = str(ser.readline(),'utf-8', errors='ignore').rstrip("\r\n")
            if "PID" in ve_string:
                mppt_raw_data[ve_string.split("\t")[0]] = ve_string.split("\t")[1]
                block_start = True

        block_complete = False

        while not block_complete:
            ve_string = str(ser.readline(),'utf-8', errors='ignore').rstrip("\r\n")
            if ve_string.split("\t")[0] == "Checksum":
                block_complete = True
                ser.close()
            else:
                mppt_raw_data[ve_string.split("\t")[0]] = ve_string.split("\t")[1]

        global_vars.mppt_data["pid"] = mppt_raw_data["PID"]
        global_vars.mppt_data["name"] = "SmartSolar MPPT 100|20"
        global_vars.mppt_data["err"] = int(mppt_raw_data["ERR"])
        global_vars.mppt_data["err_text"] = err_text[global_vars.mppt_data["err"]]
        global_vars.mppt_data["fw"] = mppt_raw_data["FW"]

        global_vars.mppt_data["load"]["v"] = int(mppt_raw_data["V"]) / 1000.0
        global_vars.mppt_data["load"]["i"] = int(mppt_raw_data["IL"]) / 1000.0
        global_vars.mppt_data["load"]["p"] = round(global_vars.mppt_data["load"]["v"] * global_vars.mppt_data["load"]["i"],2)
        if mppt_raw_data["LOAD"] == "ON":
            global_vars.mppt_data["load"]["state"] = True
        else:
            global_vars.mppt_data["load"]["state"] = False

        global_vars.mppt_data["batt"]["v"] = int(mppt_raw_data["V"]) / 1000.0
        global_vars.mppt_data["batt"]["i"] = int(mppt_raw_data["I"]) / 1000.0
        global_vars.mppt_data["batt"]["p"] = round(global_vars.mppt_data["batt"]["v"] * global_vars.mppt_data["batt"]["i"],2)
        global_vars.mppt_data["batt"]["cs"] = int(mppt_raw_data["CS"])
        global_vars.mppt_data["batt"]["cs_text"] = cs_text[global_vars.mppt_data["batt"]["cs"]]

        global_vars.mppt_data["pv"]["v"] = int(mppt_raw_data["VPV"]) / 1000.0
        global_vars.mppt_data["pv"]["p"] = int(mppt_raw_data["PPV"])
        global_vars.mppt_data["pv"]["i"] = round(global_vars.mppt_data["pv"]["p"] / global_vars.mppt_data["pv"]["v"],2)
        global_vars.mppt_data["pv"]["mppt"] = int(mppt_raw_data["MPPT"])
        global_vars.mppt_data["pv"]["mppt_text"] = mppt_text[global_vars.mppt_data["pv"]["mppt"]]

    except Exception as e:
        if ser.isOpen():
            ser.close()
        logger.error("mppt data task failed: " + str(e))

    pass

batt_voltage_normal = 12.2
batt_voltage_low = 11.8
batt_voltage_very_low = 11.5
batt_voltage_critical = 11.3
batt_voltage_sent = 0.0
batt_warning_sent = False
batt_warning_sent_time = 0
batt_warning_stage = 0
batt_warning_stage_text = {
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
    new_batt_warning_stage = 0
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
            if global_vars.mppt_data["batt"]["i"] < 0:
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
                if global_vars.mppt_data["batt"]["v"] > batt_voltage_normal:
                    new_batt_warning_stage = 0
                elif global_vars.mppt_data["batt"]["v"] > batt_voltage_low:
                    new_batt_warning_stage = 1
                elif global_vars.mppt_data["batt"]["v"] > batt_voltage_very_low:
                    new_batt_warning_stage = 2
                else:
                    new_batt_warning_stage = 3

                # Latch downwards when charging
                if new_batt_warning_stage < last_batt_warning_stage:
                    batt_warning_stage = new_batt_warning_stage

            if batt_warning_stage > last_batt_warning_stage:
                if batt_warning_stage == 1:
                    warn_sms_text = human_datetime + ": Battery voltage low! "+str(global_vars.mppt_data["batt"]["v"])+"V"
                    logger.warning("Battery voltage low! Current voltage: " + str(global_vars.mppt_data["batt"]["v"]) + "V. Sending alert SMS")
                elif batt_warning_stage == 2:
                    warn_sms_text = human_datetime + ": Battery voltage very low! "+str(global_vars.mppt_data["batt"]["v"])+"V"
                    logger.warning("Battery voltage very low! Current voltage: " + str(global_vars.mppt_data["batt"]["v"]) + "V. Sending alert SMS")
                elif batt_warning_stage == 3:
                    warn_sms_text = human_datetime + ": Battery voltage CRITICAL! "+str(global_vars.mppt_data["batt"]["v"])+"V"
                    logger.critical("Battery voltage critical! Current voltage: " + str(global_vars.mppt_data["batt"]["v"]) + "V. Sending alert SMS")
            elif ( batt_warning_stage < last_batt_warning_stage ) and batt_warning_stage == 0:
                warn_sms_text = "Battery voltage returning to normal: " + global_vars.mppt_data["batt"]["v"] + "V"
                logger.info(warn_sms_text)

            if warn_sms_text and ( unix_time_int > batt_warning_sent_time + batt_warning_interval ):
                if ( last_batt_voltage_sent - 0.1 < global_vars.mppt_data["batt"]["v"] ) or ( last_batt_voltage_sent + 0.1 > global_vars.mppt_data["batt"]["v"] ):
                    last_batt_voltage_sent = global_vars.mppt_data["batt"]["v"]
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
                batt_state_sent_time = unix_time_int
                send_sms(user_data.voltage_warn_sms_list, warn_sms_text)

            global_vars.mppt_data["batt"]["state"] = 4
            global_vars.mppt_data["batt"]["state_text"] = batt_warning_stage_text[batt_warning_stage]

        if batt_state != last_batt_state:
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

def mppt_loop():
    logger.info("Starting MPPT data loop from VE.Direct interface")
    while True:
        get_mppt_data()
        check_load_state()
        check_batt_voltage()
        time.sleep(1)
    pass
