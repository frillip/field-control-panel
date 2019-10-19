import time
import serial

def get_mppt_data():

    ser = serial.Serial(
    port='/dev/ttyUSB0',
    baudrate = 19200,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS,
    timeout=1
    )

    off = {
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

    cs = {
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

    err = {
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

    mppt = {
    0: 'Off',
    1: 'Voltage or current limited',
    2: 'MPP Tracker active'
    }

    mppt_raw_data = {}
    mppt_data = {}

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
        else:
            mppt_raw_data[ve_string.split("\t")[0]] = ve_string.split("\t")[1]

    mppt_data["pid"] = mppt_raw_data["PID"]
    mppt_data["name"] = "SmartSolar MPPT 100|20"
    if mppt_raw_data["ERR"] == "0":
        mppt_data["error"] = False
    else:
        mppt_data["error"] = True
    mppt_data["fw"] = mppt_raw_data["FW"]

    mppt_load_data = {}
    mppt_load_data["v"] = int(mppt_raw_data["V"]) / 1000.0
    mppt_load_data["i"] = int(mppt_raw_data["IL"]) / 1000.0
    mppt_load_data["p"] = round(mppt_load_data["v"] * mppt_load_data["i"],2)
    if mppt_raw_data["LOAD"] == "ON":
        mppt_load_data["state"] = True
    else:
        mppt_load_data["state"] = False

    mppt_batt_data = {}
    mppt_batt_data["v"] = int(mppt_raw_data["V"]) / 1000.0
    mppt_batt_data["i"] = int(mppt_raw_data["I"]) / 1000.0
    mppt_batt_data["p"] = round(mppt_batt_data["v"] * mppt_batt_data["i"],2)
    mppt_batt_data["cs"] = int(mppt_raw_data["CS"])
    mppt_batt_data["cs_text"] = cs[mppt_batt_data["cs"]]

    mppt_pv_data = {}
    mppt_pv_data["v"] = int(mppt_raw_data["VPV"]) / 1000.0
    mppt_pv_data["p"] = int(mppt_raw_data["PPV"])
    mppt_pv_data["i"] = round(mppt_pv_data["p"] / mppt_pv_data["v"],2)
    mppt_pv_data["mppt"] = int(mppt_raw_data["MPPT"])
    mppt_pv_data["mppt_text"] = mppt[mppt_pv_data["mppt"]]

    mppt_data["load"] = mppt_load_data
    mppt_data["batt"] = mppt_batt_data
    mppt_data["pv"] = mppt_pv_data

    return mppt_data
