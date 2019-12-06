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
        while True:
            ve_string = str(ser.readline(),'utf-8', errors='ignore').rstrip("\r\n")
            field["label"] = ve_string.split("\t")[0]
            field["data"] = ve_string.split("\t")[1]

            if field["label"] == "PID":
                # Product ID
                global_vars.mppt_data["pid"] = field["data"]
                # Could look this up from a table based on PID, but there's no point unless I combine this and the BMV function...
                global_vars.mppt_data["name"] = "SmartSolar MPPT 100|20"
            elif field["label"] == "ERR":
                # Error value and meaning
                global_vars.mppt_data["err"] = int(field["data"])
                global_vars.mppt_data["err_text"] = err_text[global_vars.mppt_data["err"]]
            elif field["label"] == "FW":
                # Firmware version
                global_vars.mppt_data["fw"] = field["data"]
            elif field["label"] == "V":
                # Battery voltage
                global_vars.mppt_data["batt"]["v"] = int(field["data"]) / 1000.0
                global_vars.mppt_data["load"]["v"] = int(field["data"]) / 1000.0
            elif field["label"] == "IL":
                # Load current
                global_vars.mppt_data["load"]["i"] = int(field["data"]) / 1000.0
            elif field["label"] == "LOAD":
                # Load status
                if field["data"] == "ON":
                    global_vars.mppt_data["load"]["state"] = True
                else:
                    global_vars.mppt_data["load"]["state"] = False
            elif field["label"] == "I":
                # Battery current
                global_vars.mppt_data["batt"]["i"] = int(field["data"]) / 1000.0
            elif field["label"] == "CS":
                # Battery charging status and meaning
                global_vars.mppt_data["batt"]["cs"] = int(field["data"])
                global_vars.mppt_data["batt"]["cs_text"] = cs_text[global_vars.mppt_data["batt"]["cs"]]
            elif field["label"] == "VPV":
                # PV array voltage
                global_vars.mppt_data["pv"]["v"] = int(field["data"]) / 1000.0
            elif field["label"] == "PPV":
                # PV array power
                global_vars.mppt_data["pv"]["p"] = int(field["data"])
            elif field["label"] == "MPPT":
                # MPPT status and meaning
                global_vars.mppt_data["pv"]["mppt"] = int(field["data"])
                global_vars.mppt_data["pv"]["mppt_text"] = mppt_text[global_vars.mppt_data["pv"]["mppt"]]
            elif field["label"] == "H20":
                # Today's total yield in Wh
                global_vars.mppt_data["pv"]["yield"] = int(field["data"]) * 10
            elif field["label"] == "Checksum":
                # We've reached the end of the block, so presumably everything has been read
                # These are computed here, rather than being read from the MPPT
                global_vars.mppt_data["load"]["p"] = round(global_vars.mppt_data["load"]["v"] * global_vars.mppt_data["load"]["i"],2)
                global_vars.mppt_data["batt"]["p"] = round(global_vars.mppt_data["batt"]["v"] * global_vars.mppt_data["batt"]["i"],2)
                global_vars.mppt_data["pv"]["i"] = round(global_vars.mppt_data["pv"]["p"] / global_vars.mppt_data["pv"]["v"],2)

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
        while True:
            ve_string = str(ser.readline(),'utf-8', errors='ignore').rstrip("\r\n")
            field["label"] = ve_string.split("\t")[0]
            field["data"] = ve_string.split("\t")[1]

            if field["label"] == "PID":
                # Product ID
                global_vars.bmv_data["pid"] = field["data"]
                # Could look this up from a table based on PID, but there's no point unless I combine this and the MPPT function...
                global_vars.bmv_data["name"] = "BMV-712 Smart"
            elif field["label"] == "FW":
                # FIrmware version
                global_vars.bmv_data["fw"] = field["data"]
            elif field["label"] == "V":
                 # Battery voltage, V
                global_vars.bmv_data["batt"]["v"] = int(field["data"]) / 1000.0
            elif field["label"] == "I":
                # Battery current, A, negative indicates discharge, positive indicates charge
                global_vars.bmv_data["batt"]["i"] = int(field["data"]) / 1000.0
            elif field["label"] == "P":
                # Battery power, W, negative indicates discharge, positive indicates charge
                global_vars.bmv_data["batt"]["p"] = int(field["data"])
            elif field["label"] == "T":
                # Battery temperature, degC, may be replaced with midpoint voltage in the future
                # in which case BME280 temperature can be used as an estimate
                global_vars.bmv_data["batt"]["t"] = int(field["data"])
            elif field["label"] == "SOC":
                # State of charge ,%
                global_vars.bmv_data["batt"]["soc"] = int(field["data"]) / 10.0
            elif field["label"] == "TTG":
                # Time left on battery power, s
                global_vars.bmv_data["batt"]["ttg"] = int(field["data"])
            elif field["label"] == "CE":
                # Amount of charge consumed, Ah
                global_vars.bmv_data["batt"]["charge_consumed"] = int(field["data"]) / 1000.0
            elif field["label"] == "Alarm":
                # Alarm condition
                if field["data"] == "ON":
                    global_vars.bmv_data["alarm"] = True
                else:
                    global_vars.bmv_data["alarm"] = False
                # Needs bitmasking done as multiple alarms can be present
                #global_vars.bmv_data["alarm_text"] = alarm_text[global_vars.bmv_data["AR"]]
            elif field["label"] == "Relay":
                # Relay state
                if field["data"] == "ON":
                    global_vars.bmv_data["relay"] = True
                else:
                    global_vars.bmv_data["relay"] = False

            elif field["label"] == "H1":
                # Depth of the deepest discharge, Ah
                global_vars.bmv_data["stats"]["deepest_discharge"] = int(field["data"]) / 1000.0
            elif field["label"] == "H2":
                # Depth of the last discharge, Ah
                global_vars.bmv_data["stats"]["last_discharge"] = int(field["data"]) / 1000.0
            elif field["label"] == "H3":
                # Depth of the average discharge, Ah
                global_vars.bmv_data["stats"]["average_discharge"] = int(field["data"]) / 1000.0
            elif field["label"] == "H4":
                # Number of charge cycles
                global_vars.bmv_data["stats"]["cycles"] = int(field["data"])
            elif field["label"] == "H5":
                # Number of full discharges
                global_vars.bmv_data["stats"]["full_discharges"] = int(field["data"])
            elif field["label"] == "H6":
                # Cumulative Amp Hours drawn, Ah
                global_vars.bmv_data["stats"]["total_charge_consumed"] = int(field["data"]) / 1000.0
            elif field["label"] == "H7":
                # Minimum battery voltage, V
                global_vars.bmv_data["stats"]["min_voltage"] = int(field["data"]) / 1000.0
            elif field["label"] == "H8":
                # Maximum battery voltage, V
                global_vars.bmv_data["stats"]["max_voltage"] = int(field["data"]) / 1000.0
            elif field["label"] == "H9":
                # Number of seconds since last full charge, s
                global_vars.bmv_data["batt"]["discharge_time"] = int(field["data"])
            elif field["label"] == "H10":
                # Number of automatic synchronizations (24V system only)
                global_vars.bmv_data["stats"]["sync_count"] = int(field["data"])
            elif field["label"] == "H11":
                # Number of low main voltage alarms
                global_vars.bmv_data["stats"]["lv_alarm_count"] = int(field["data"])
            elif field["label"] == "H12":
                # Number of high main voltage alarms
                global_vars.bmv_data["stats"]["hv_alarm_count"] = int(field["data"])
            elif field["label"] == "H17":
                # Amount of discharged energy, Wh
                global_vars.bmv_data["batt"]["energy_discharged"] = int(field["data"]) * 10
            elif field["label"] == "H18":
                # Amount of charged energy, Wh
                global_vars.bmv_data["batt"]["energy_charged"] = int(field["data"]) * 10

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
