import smbus2
import bme280
import global_vars
import logging
import colorlog

bme_port = 1 # Yes
bme_address = 0x76 # Cheap BME280s are 0x76, Adafruit is 0x77
bme_bus = smbus2.SMBus(bme_port)

handler = colorlog.StreamHandler()
handler.setFormatter(global_vars.log_format)
logger = colorlog.getLogger("bme280")
logger.addHandler(handler)
logger.setLevel(logging.INFO)

def get_bme_data():
    global bme_bus
    global bme_address

    bme_data = {}
    try:
        bme280.load_calibration_params(bme_bus,bme_address)

        bme_raw_data = bme280.sample(bme_bus,bme_address)
        bme_data['h'] = round(bme_raw_data.humidity,1)
        bme_data['p'] = round(bme_raw_data.pressure,1)
        bme_data['t'] = round(bme_raw_data.temperature,1)
        bme_data['e'] = False

    except Exception as e:
        logger.error("Failed to get data from BME280: " + str(e))
        bme_data['e'] = True

    global_vars.bme_data = bme_data

    pass
