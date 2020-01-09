import smbus2
import bme280
import global_vars
from yaml_config import config
import logging
import colorlog

bme_bus = None

handler = colorlog.StreamHandler()
handler.setFormatter(global_vars.log_format)
logger = colorlog.getLogger("bme280")
logger.addHandler(handler)
logger.setLevel(global_vars.log_level)

def get_bme_data():

    # Initial set up required
    global bme_bus
    if not bme_bus:
        # Set up the i2c bus for the BME280
        bme_bus = smbus2.SMBus(config['bme']['i2c_port'])
        # Load some data
        bme280.load_calibration_params(bme_bus,config['bme']['i2c_address'])

    try:
        # Read some data
        bme_raw_data = bme280.sample(bme_bus,config['bme']['i2c_address'])

        # Deposit it into the global dict
        global_vars.bme_data['h'] = round(bme_raw_data.humidity,1)
        global_vars.bme_data['p'] = round(bme_raw_data.pressure,1)
        global_vars.bme_data['t'] = round(bme_raw_data.temperature,1)

    except Exception as e:
        # Error has occurred, log it
        logger.error("Failed to get data from BME280: " + str(e))

    pass
