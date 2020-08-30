import smbus2
import bme280
import gpsd
from timezonefinder import TimezoneFinder
from tsl2561 import TSL2561
import RPi.GPIO as GPIO
import LIS3DH
from ina260.controller import Controller
from datetime import datetime
import time
from sms_sender import send_sms
from system_status import system_state
import global_vars
from yaml_config import config
import logging
import colorlog

i2c_bus = None
tsl = None
accel = None
ina = None

logger = colorlog.getLogger(__name__)
logger.addHandler(global_vars.file_handler)
logger.addHandler(global_vars.handler)
logger.setLevel(global_vars.log_level)

bme280_data = {}
tsl2561_data = {}
lis3dh_data = {}
ina260_data = {}
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
    global accel
    global ina

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

            tsl2561_data['door_open'] = False
            tsl2561_data['door_open_count'] = 0
            tsl2561_data['last_door_open_count'] = 0
            tsl2561_data['last_door_open'] = 0
            tsl2561_data['last_door_open_timestamp'] = 0
            tsl2561_data['door_open_warn'] = False

            # Populate some data
            get_tsl2561_data()
        else:
            tsl2561_data['enabled'] = False

        if config['sensors']['lis3dh_enable']:
            lis3dh_data['enabled'] = True
            # Start the accelerometer and set up the interrupt
            logger.info('Starting LIS3DH accelerometer')
            accel = LIS3DH.Accelerometer('i2c',i2cAddress = config['sensors']['lis3dh_address'])
            accel.set_ODR(odr=10, powerMode='normal')
            accel.axis_enable(x='on',y='on',z='on')
            accel.set_highpass_filter('autoreset',0x01,0x00,0x00,0x00,0x01)
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
                # set INT1_DURATION  to 100ms
                accel.set_int1_duration(0)
                # on INT1_CFG enable 6D positioning, X, Y & Z (H & L)
                accel.set_int1_config(aoi=0, d6=1, zh=1, zl=1, yh=1, yl=1, xh=1, xl=1)
                # Get some data
                lis3dh_data['interrupt_state'] = False
                lis3dh_data['interrupt_count'] = 0
                lis3dh_data['last_interrupt_count'] = 0
                lis3dh_data['last_interrupt'] = 0
                lis3dh_data['last_interrupt_timestamp'] = 0
                lis3dh_data['motion_warn'] = False
            else:
                info.warn('No interrput pin specified for accelerometer! Sensor will be polled but may miss events!')

            get_lis3dh_data()
        else:
            lis3dh_data['enabled'] = False

        if config['sensors']['ina260_enable']:
            ina260_data['enabled'] = True
            # Load some data into the BME280
            logger.info('Starting INA260 sensor')
            ina = Controller(address=config['sensors']['ina260_address'],channel=i2c_bus)

            # Populate some data
            get_ina260_data()
        else:
            ina260_data['enabled'] = False

        if config['sensors']['gps_enable']:
            gps_data['enabled'] = True
            gps_data['mode'] = 0
            gps_data['mode_text'] = gps_mode_text[gps_data['mode']]
            # Connect to the GPSd daemon
            logger.info('Connecting to GPSd')
            gpsd.connect()
            # Get gpsd mode first
            packet = gpsd.get_current()
            gps_data['mode'] = packet.mode
            gps_data['mode_text'] = gps_mode_text[gps_data['mode']]

            # Then populate the rest of the data
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
    unix_time_int = int(time.time())
    now_iso_stamp = datetime.now().replace(microsecond=0).isoformat()

    if config['sensors']['tsl2561_enable']:
        try:
            tsl2561_data['lux'] = tsl.lux()
            tsl2561_data['broad_counts'],tsl2561_data['ir_counts'] = tsl._get_luminosity()
            tsl2561_data['gain'] = tsl.gain
            if not tsl2561_data['gain']:
                tsl2561_data['gain'] = 1

            if unix_time_int > ( tsl2561_data['last_door_open_timestamp'] + 3 ) and tsl2561_data['door_open_count']:
                tsl2561_data['door_open'] = False
                tsl2561_data['door_open_warn'] = False
                tsl2561_data['last_door_open_count'] = tsl2561_data['door_open_count']
                tsl2561_data['door_open_count'] = 0

            if tsl2561_data['lux'] > 10:
                tsl2561_data['door_open'] = True

                if unix_time_int < ( tsl2561_data['last_door_open_timestamp'] + 3 ):
                    tsl2561_data['door_open_count'] += 1
                else:
                    tsl2561_data['door_open_count'] = 1

                tsl2561_data['last_door_open'] = now_iso_stamp
                tsl2561_data['last_door_open_timestamp'] = unix_time_int

                if tsl2561_data['door_open_count'] > 5 and not tsl2561_data['door_open_warn'] and config['sensors']['tsl2561_warn_enable']:
                    logger.critical('5 lux measurements exceed door open conditions!')
                    tsl2561_data['door_open_warn'] = True
                    if not system_state['maintenance_mode']:
                        human_datetime = datetime.now().strftime('%d/%m/%Y %H:%M')
                        warn_sms_text = human_datetime + ': Door open event detected!'
                        send_sms(config['sensors']['tsl2561_sms_list'], warn_sms_text)
                    else:
                        logger.warning("System in maintenance mode, no warning SMS sent")

        except Exception as e:
            # Error has occurred, log it
            logger.error("Failed to get data from TSL2561: " + str(e))

    else:
        logger.warn('Request to read TSL2561 data, but not enabled in config')


def get_lis3dh_data():
    unix_time_int = int(time.time())
    now_iso_stamp = datetime.now().replace(microsecond=0).isoformat()

    if config['sensors']['lis3dh_enable']:
        try:
            lis3dh_data['x'] = accel.x_axis_reading()
            lis3dh_data['y']= accel.y_axis_reading()
            lis3dh_data['z'] = accel.z_axis_reading()
            lis3dh_data['interrupt'] = accel.get_int1_status()
            if unix_time_int > ( lis3dh_data['last_interrupt_timestamp'] + 3 ) and lis3dh_data['interrupt_count']:
                lis3dh_data['interrupt_state'] = False
                lis3dh_data['motion_warn'] = False
                lis3dh_data['last_interrupt_count'] = lis3dh_data['interrupt_count']
                lis3dh_data['interrupt_count'] = 0
        except Exception as e:
            # Error has occurred, log it
            logger.error("Failed to get data from LIS3DH: " + str(e))
    else:
        logger.warn('Request to read LIS3DH data, but not enabled in config')

def accel_isr(channel):
    unix_time_int = int(time.time())
    now_iso_stamp = datetime.now().replace(microsecond=0).isoformat()

    try:
        if channel != config['sensors']['lis3dh_interrupt_pin']:
            return

        get_lis3dh_data()
        if lis3dh_data['interrupt']:
            if unix_time_int < ( lis3dh_data['last_interrupt_timestamp'] + 3 ):
                lis3dh_data['interrupt_count'] += 1
            else:
                lis3dh_data['interrupt_count'] = 1
            lis3dh_data['interrupt_state'] = True
            lis3dh_data['last_interrupt'] = now_iso_stamp
            lis3dh_data['last_interrupt_timestamp'] = unix_time_int
            if lis3dh_data['interrupt_count'] > 5 and not lis3dh_data['motion_warn'] and config['sensors']['lis3dh_warn_enable']:
                logger.critical('5 motion events detected!')
                lis3dh_data['motion_warn'] = True
                if not system_state['maintenance_mode']:
                    human_datetime = datetime.now().strftime('%d/%m/%Y %H:%M')
                    warn_sms_text = human_datetime + ': Motion event detected!'
                    send_sms(config['sensors']['lis3dh_sms_list'], warn_sms_text)
                else:
                    logger.warning("System in maintenance mode, no warning SMS sent")


    except Exception as e:
        # Error has occurred, log it
        logger.error("LIS3DH interrupt triggered but ISR failed: " + str(e))


def get_ina260_data():

    if config['sensors']['ina260_enable']:
        try:
            # Read some data and deposit it into the dict
            ina260_data['v'] = round(ina.voltage(),2)
            ina260_data['i'] = round(ina.current(),2)
            ina260_data['p'] = round(ina.power(),2)

        except Exception as e:
            # Error has occurred, log it
            logger.error("Failed to get data from INA260: " + str(e))
    else:
        logger.warn('Request to read INA260 data, but not enabled in config')


def get_gps_data():

    if config['sensors']['gps_enable']:
        try:
            # Reinitialise gpsd connection if it's broken for some reason
            if not gps_data['mode']:
                gpsd.connect()

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
                gps_data['timezone'] = TimezoneFinder().timezone_at(lng=packet.lon, lat=packet.lat)
                gps_data['latitude'] = round(packet.lat,4)
                gps_data['longitude'] = round(packet.lon,4)
                gps_data['speed'] = int(packet.speed())
            else:
                gps_data['time'] = None
                gps_data['time_local'] = None
                gps_data['timezone'] = None
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
            gps_data.clear()
            gps_data['enabled'] = True
            gps_data['mode'] = 0
            gps_data['mode_text'] = gps_mode_text[gps_data['mode']]

    else:
        logger.warn('Request to read GPS data, but not enabled in config')


def get_sensor_data():
    if config['sensors']['bme280_enable']:
        get_bme280_data()
    if config['sensors']['tsl2561_enable']:
        get_tsl2561_data()
    if config['sensors']['lis3dh_enable']:
        get_lis3dh_data()
    if config['sensors']['ina260_enable']:
        get_ina260_data()
    if config['sensors']['gps_enable']:
        get_gps_data()
