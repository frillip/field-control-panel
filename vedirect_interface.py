import time
import serial
import global_vars
import logging
import colorlog
from system_status import check_batt_voltage,check_load_state

handler = colorlog.StreamHandler()
handler.setFormatter(global_vars.log_format)
logger = colorlog.getLogger(__name__)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

mppt_tty_dev = '/dev/ttyUSB1'
bmv_tty_dev = '/dev/ttyUSB0'
baudrate = 19200

alarm_text = {
0x0001: 'Low voltage',
0x0002: 'High voltage',
0x0004: 'Low SOC',
0x0008: 'Low Starter Voltage',
0x0010: 'High Starter Voltage',
0x0020: 'Low Temperature',
0x0040: 'High Temperature',
0x0080: 'Mid Voltage',
0x0100: 'Overload',
0x0200: 'DC-ripple',
0x0400: 'Low V AC out',
0x0800: 'High V AC out',
0x1000: 'Short circuit',
0x2000: 'BMS Lockout'
}

off_text = {
0x001: 'No input power',
0x0002: 'Switched off (power switch)',
0x0004: 'Switched off (register)',
0x0008: 'Remote input',
0x0010: 'Protection active',
0x0020: 'Paygo',
0x0040: 'BMS',
0x0080: 'Engine shutdown detection',
0x0100: 'Analysing input voltage'
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
        global_vars.mppt_data["pv"]["yield"] = int(mppt_raw_data["H20"]) * 10

    except Exception as e:
        if ser.isOpen():
            ser.close()
        logger.error("mppt data task failed: " + str(e))

    pass


def get_bmv_data():

    bmv_raw_data = {}

    try:
        ser = serial.Serial()
        ser.port = bmv_tty_dev
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
# Data from the BMV comes in 2 blocks
            if "PID" in ve_string or "H1\t" in ve_string:
                if "PID" in ve_string:
                    block_id = 1
                elif "H1" in ve_string:
                    block_id = 2
                bmv_raw_data[ve_string.split("\t")[0]] = ve_string.split("\t")[1]
                block_start = True

        block_complete = False

        while not block_complete:
            ve_string = str(ser.readline(),'utf-8', errors='ignore').rstrip("\r\n")
            if ve_string.split("\t")[0] == "Checksum":
                block_complete = True
                ser.close()
            else:
                bmv_raw_data[ve_string.split("\t")[0]] = ve_string.split("\t")[1]

        if block_id == 1:
            global_vars.bmv_data["pid"] = bmv_raw_data["PID"]
            global_vars.bmv_data["name"] = "BMV-712 Smart"
            global_vars.bmv_data["fw"] = bmv_raw_data["FW"]
            global_vars.bmv_data["batt"]["v"] = int(bmv_raw_data["V"]) / 1000.0
            global_vars.bmv_data["batt"]["t"] = int(bmv_raw_data["T"])
            global_vars.bmv_data["batt"]["i"] = int(bmv_raw_data["I"]) / 1000.0
            global_vars.bmv_data["batt"]["p"] = int(bmv_raw_data["P"])
            global_vars.bmv_data["batt"]["soc"] = int(bmv_raw_data["SOC"]) / 10.0
            global_vars.bmv_data["batt"]["ttg"] = int(bmv_raw_data["TTG"])
            global_vars.bmv_data["batt"]["charge_consumed"] = int(bmv_raw_data["CE"]) / 1000.0
            if bmv_raw_data["Alarm"] == "ON":
                global_vars.bmv_data["alarm"] = True
            else:
                global_vars.bmv_data["alarm"] = False
# Needs bitmasking done as multiple alarms can be present
#            global_vars.bmv_data["alarm_text"] = alarm_text[global_vars.bmv_data["AR"]]
            if bmv_raw_data["Relay"] == "ON":
                global_vars.bmv_data["relay"] = True
            else:
                global_vars.bmv_data["relay"] = False
        elif block_id == 2:
            global_vars.bmv_data["stats"]["deepest_discharge"] = int(bmv_raw_data["H1"]) / 1000.0
            global_vars.bmv_data["stats"]["last_discharge"] = int(bmv_raw_data["H2"]) / 1000.0
            global_vars.bmv_data["stats"]["average_discharge"] = int(bmv_raw_data["H3"]) / 1000.0
            global_vars.bmv_data["stats"]["cycles"] = int(bmv_raw_data["H4"])
            global_vars.bmv_data["stats"]["full_discharges"] = int(bmv_raw_data["H5"])
            global_vars.bmv_data["stats"]["total_charge_consumed"] = int(bmv_raw_data["H6"]) / 1000.0
            global_vars.bmv_data["stats"]["min_voltage"] = int(bmv_raw_data["H7"]) / 1000.0
            global_vars.bmv_data["stats"]["max_voltage"] = int(bmv_raw_data["H8"]) / 1000.0
            global_vars.bmv_data["stats"]["sync_count"] = int(bmv_raw_data["H10"])
            global_vars.bmv_data["stats"]["lv_alarm_count"] = int(bmv_raw_data["H11"])
            global_vars.bmv_data["stats"]["hv_alarm_count"] = int(bmv_raw_data["H12"])
            global_vars.bmv_data["batt"]["discharge_time"] = int(bmv_raw_data["H9"])
            global_vars.bmv_data["batt"]["energy_discharged"] = int(bmv_raw_data["H17"]) * 10
            global_vars.bmv_data["batt"]["energy_charged"] = int(bmv_raw_data["H18"]) * 10

    except Exception as e:
        if ser.isOpen():
            ser.close()
        logger.error("bmv data task failed: " + str(e))

    pass

def mppt_loop():
    logger.info("Starting MPPT data loop from VE.Direct interface")
    while True:
        get_mppt_data()
        check_load_state()
        check_batt_voltage()
        time.sleep(0.5)
    pass

def bmv_loop():
    logger.info("Starting BMV data loop from VE.Direct interface")
    while True:
# Need to install BMV712 first!
        get_bmv_data()
# Needs rewrite first
#        check_batt_voltage()
        time.sleep(0.5)
    pass
