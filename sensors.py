import smbus2
import bme280
import gpsd
from tsl2561 import TSL2561
import RPi.GPIO as GPIO
# import LIS3DH
import global_vars
from yaml_config import config
import logging
import colorlog

i2c_bus = None
tsl = None

handler = colorlog.StreamHandler()
handler.setFormatter(global_vars.log_format)
logger = colorlog.getLogger("sensors")
logger.addHandler(handler)
logger.setLevel(global_vars.log_level)

bme280_data = {}
tsl2561_data = {}
lis3dh_data = {}
gps_data = {}

gps_mode_text = {
0: 'No mode',
1: 'No fix',
2: '2D fix',
3: '3D fix',
}

def init_sensors():

    global i2c_bus
    global tsl

    try:
        # Init the i2c bus
        i2c_bus = smbus2.SMBus(config['sensors']['i2c_port'])

        if config['sensors']['bme280_enable']:
            bme280_data['enabled'] = True
            # Load some data into the BME280
            logger.info('Starting BME280 sensor')
            bme280.load_calibration_params(i2c_bus,config['sensors']['bme280_address'])

            # Populate some data
            get_bme280_data()
        else:
            bme280_data['enabled'] = False

        if config['sensors']['tsl2561_enable']:
            tsl2561_data['enabled'] = True
            # Start the TSL2561 sensor
            logger.info('Starting TSL2561 ambient light sensor')
            tsl = TSL2561(gain=config['sensors']['tsl2561_gain'],integration_time=config['sensors']['tsl2561_integration_time'])

            # Populate some data
            get_tsl2561_data()
        else:
            tsl2561_data['enabled'] = False

        if config['sensors']['lis3dh_enable']:
            lis3dh_data['enabled'] = True
            # Start the accelerometer and set up the interrupt
            logger.info('Starting LIS3DH accelerometer')
            """
            accel = LIS3DH.Accelerometer('i2c',i2cAddress = config['sensors']['lis3dh_address'])
            accel.set_ODR(odr=50, powerMode='normal')
            accel.axis_enable(x='on',y='on',z='on')
            accel.interrupt_high_low('low')
            accel.latch_interrupt('on')
            accel.set_BDU('on')
            accel.set_scale()

            if config['sensors']['lis3dh_interrupt_pin']:
                # GPIO setup
                GPIO.setmode(GPIO.BCM)
                GPIO.setwarnings(False)
                # Set up port as an input with pullup enabled
                GPIO.setup(config['sensors']['lis3dh_interrupt_pin'], GPIO.IN, pull_up_down=GPIO.PUD_UP)
                # Add a detection event and callback for falling edge on int pin
                GPIO.add_event_detect(config['sensors']['lis3dh_interrupt_pin'], GPIO.FALLING, callback=accel_isr)

                # Accelerometer interrupt setup
                # turn on AOI1 interrupt
                accel.set_int1_pin(click=0,aoi1=1, aoi2=0, drdy1=0, drdy2=0, wtm=0, overrun=0)
                # set INT1_THS to 256mg
                accel.set_int1_threshold(256)
                # set INT1_DURATION  to 0ms
                accel.set_int1_duration(0)
                # on INT1_CFG enable 6D positioning, X, Y & Z (H & L)
                accel.set_int1_config(aoi=1, d6=1, zh=1, zl=1, yh=1, yl=1, xh=1, xl=1)
            else:
                info.warn('No interrput pin specified for accelerometer! Sensor will be polled but may miss events!')
            """

        else:
            lis3dh_data['enabled'] = False

        if config['sensors']['gps_enable']:
            gps_data['enabled'] = True
            # Connect to the GPSd daemon
            logger.info('Connecting to GPSd')
            gpsd.connect()

            # Populate some data
            get_gps_data()
        else:
            gps_data['enabled'] = False

    except Exception as e:
        logger.error("Failed to set up sensors: " + str(e))


def get_bme280_data():

    if config['sensors']['bme280_enable']:
        try:
            # Read some data
            bme_raw_data = bme280.sample(i2c_bus,config['sensors']['bme280_address'])

            # Deposit it into the global dict
            bme280_data['h'] = round(bme_raw_data.humidity,1)
            bme280_data['p'] = round(bme_raw_data.pressure,1)
            bme280_data['t'] = round(bme_raw_data.temperature,1)

        except Exception as e:
            # Error has occurred, log it
            logger.error("Failed to get data from BME280: " + str(e))
    else:
        logger.warn('Request to read BME280 data, but not enabled in config')


def get_tsl2561_data():
    if config['sensors']['tsl2561_enable']:
        try:
            tsl2561_data['lux'] = tsl.lux()
            tsl2561_data['broad_counts'],tsl2561_data['ir_counts'] = tsl._get_luminosity()
            tsl2561_data['gain'] = tsl.gain
            if not tsl2561_data['gain']:
                tsl2561_data['gain'] = 1

        except Exception as e:
            # Error has occurred, log it
            logger.error("Failed to get data from TSL2561: " + str(e))

    else:
        logger.warn('Request to read TSL2561 data, but not enabled in config')


def get_lis3dh_data():
    if config['sensors']['lis3dh_enable']:
        pass

    else:
        logger.warn('Request to read LIS3DH data, but not enabled in config')


def get_gps_data():

    if config['sensors']['gps_enable']:
        try:
            # Read some data
            packet = gpsd.get_current()
            # Deposit it into the global dict
            gps_data['mode'] = packet.mode
            gps_data['mode_text'] = gps_mode_text[gps_data['mode']]
            gps_data['sats'] = packet.sats
            gps_data['sats_valid'] = packet.sats_valid

            # Present some information if we have a fix
            if ( gps_data['mode'] >= 2 ):
                gps_data['time'] = packet.get_time().replace(tzinfo=None,microsecond=0).isoformat()
                gps_data['time_local'] = packet.get_time(local_time=True).replace(tzinfo=None,microsecond=0).isoformat()
                gps_data['latitude'] = round(packet.lat,4)
                gps_data['longitude'] = round(packet.lon,4)
                gps_data['speed'] = int(packet.speed())
            else:
                gps_data['time'] = None
                gps_data['time_local'] = None
                gps_data['latitude'] = None
                gps_data['longitude'] = None
                gps_data['speed'] = None

            # Information below is only obtainable from a 3D fix
            if ( gps_data['mode'] >= 3 ):
                gps_data['altitude'] = int(packet.alt)
            else:
                gps_data['altitude'] = None

        except Exception as e:
            # Error has occurred, log it
            logger.error("Failed to get GPS data: " + str(e))

    else:
        logger.warn('Request to read GPS data, but not enabled in config')


def get_sensor_data():
    get_bme280_data()
    get_tsl2561_data()
    get_lis3dh_data()
    get_gps_data()
