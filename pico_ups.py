import global_vars
import smbus2
import RPi.GPIO as GPIO
from time import sleep
from yaml_config import config
# from system_status import check_ups_status
import logging
import colorlog

from pprint import pprint

handler = colorlog.StreamHandler()
handler.setFormatter(global_vars.log_format)
logger = colorlog.getLogger('picoups')
logger.addHandler(handler)
logger.setLevel(global_vars.log_level)

CLOCK_PIN = 27
PULSE_PIN = 22
BOUNCE_TIME = 30
sqwave = True
pulse_count = 0
pulse_errors = 0
pico_bus = None

ups_data = {}
ups_data['batt'] = {}
ups_data['fan'] = {}

ups_mode_text = {
0x01: 'External',
0x02: 'Battery',
}

fan_mode_text = {
0x00: 'Off',
0x01: 'On',
0x02: 'Auto',
}

batt_type_text = {
0x53: 'LiPO',
0x46: 'LiFePO4',
0x49: 'Li-Ion',
0x48: 'NiMH',
0x4C: 'SAL',
0x50: 'LiPO',
0x51: 'LiFePO4',
0x4F: 'Li-Ion',
0x4D: 'NiMH',
0x41: 'SAL',
}

def setup_pulsetrain():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(CLOCK_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(PULSE_PIN, GPIO.OUT, initial=sqwave)
    GPIO.add_event_detect(CLOCK_PIN, GPIO.FALLING, callback=isr, bouncetime=BOUNCE_TIME)

def isr(channel):
    global pulse_count
    global pulse_errors
    # This test is here because the user *might* have another HAT plugged in or another circuit that produces a
    # falling-edge signal on another GPIO pin.
    if channel != CLOCK_PIN:
        return

    # we can get the state of a pin with GPIO.input even when it is currently configured as an output
    sqwave = not GPIO.input(PULSE_PIN)

    # set pulse pin low before changing it to input to look for shutdown signal
    GPIO.output(PULSE_PIN, False)
    GPIO.setup(PULSE_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    if not GPIO.input(PULSE_PIN):
        pulse_errors += 1
        logger.warn('Power went off... do something maybe?')
    else:
        pulse_count += 1

    # change pulse pin back to output with flipped state
    GPIO.setup(PULSE_PIN, GPIO.OUT, initial=sqwave)
#
def setup_ups():
    global pico_bus
    try:
        logger.info('Loading configuration to PIco UPS')
        # If it's the first run, i2c bus needs initialising
        if not pico_bus:
            pico_bus = smbus2.SMBus(config['picoups']['i2c_port'])

        # Set the battery type
        pico_bus.write_byte_data(0x6b, 0x07, config['picoups']['battery_type'])

        # Set fan threshold temperature (if both fan and to92 are present)
        if config['picoups']['fan_enable'] and config['picoups']['to92_enable']:
            pico_bus.write_byte_data(0x6b, 0x14, config['picoups']['fan_threshold_temp'])

        # Get some data
        get_ups_data()

    except Exception as e:
        logger.error('Failed to set up UPS: ' + str(e))

def get_ups_data():
    global pico_bus
    try:
        if not pico_bus:
            pico_bus = smbus2.SMBus(1)

        # Read all the useful data from the UPS
        ups_data['pcb'] = format(pico_bus.read_byte_data(0x69, 0x24),"02x")
        ups_data['boot'] = format(pico_bus.read_byte_data(0x69, 0x25),"02x")
        ups_data['fw'] = format(pico_bus.read_byte_data(0x69, 0x26),"02x")
        ups_data['mode'] =  pico_bus.read_byte_data(0x69, 0x00)
        ups_data['mode_text'] = ups_mode_text[ups_data['mode']]
        ups_data['v'] = float(format(pico_bus.read_word_data(0x69, 0x0A),"04x"))/100
        # This is the built in NTC-1 sensor
        ups_data['t'] = int(format(pico_bus.read_byte_data(0x69, 0x1B),"02x"))
        ups_data['alive_count'] = pico_bus.read_word_data(0x69, 0x22)
        # Read fan data if present
        if config['picoups']['fan_enable']:
            ups_data['fan']['mode'] = pico_bus.read_byte_data(0x6B, 0x11)
            ups_data['fan']['mode_text'] = fan_mode_text[ups_data['fan']['mode']]
            ups_data['fan']['speed'] = int(pico_bus.read_byte_data(0x6b, 0x12))
            ups_data['fan']['state'] = bool(pico_bus.read_byte_data(0x6b, 0x13))
            # Read TO-92 data if present
            if config['picoups']['to92_enable']:
                ups_data['fan']['t'] = int(format(pico_bus.read_byte_data(0x69, 0x1C),"02x"))
                ups_data['fan']['threshold_t'] = int(format(pico_bus.read_byte_data(0x6b, 0x14),"02x"))
        # This is set in config, but probably a decent idea to read it back to double check
        ups_data['batt']['type'] = pico_bus.read_byte_data(0x6b, 0x07)
        # Decode the raw value to human-reable text
        ups_data['batt']['type_text'] = batt_type_text[ups_data['batt']['type']]
        # Read the battery data
        ups_data['batt']['v'] = float(format(pico_bus.read_word_data(0x69, 0x08),"04x"))/100
        # This might be current? Datasheet suggests it but might not be properly implemented
        ups_data['batt']['i'] = float(format(pico_bus.read_word_data(0x69, 0x10),"04x"))/100
        ups_data['batt']['p'] = round(ups_data['batt']['v'] * ups_data['batt']['i'],2)
        # Charger IC state, only reads enabled if the battery is actively been charged
        ups_data['batt']['charger_state'] = bool(pico_bus.read_word_data(0x69, 0x20))

        # Set the charger state text based on power source and charger IC status
        if (not ups_data['batt']['charger_state'] and ups_data['mode'] == 0x01):
            ups_data['batt']['charger_state_text'] = 'Charged'
        elif (ups_data['batt']['charger_state'] and ups_data['mode'] == 0x01):
            ups_data['batt']['charger_state_text'] = 'Charging'
        elif (ups_data['mode'] == 0x02):
            ups_data['batt']['charger_state_text'] = 'Discharging'

        # Guess the SoC based on battery chemistry and voltage
        if ups_data['batt']['type_text'] == 'Li-Ion':
            ups_data['batt']['soc'] = int(((ups_data['batt']['v']-3.4)/0.899)*100)
        elif ups_data['batt']['type_text'] == 'LiPo':
            ups_data['batt']['soc'] = int(((ups_data['batt']['v']-3.4)/0.899)*100)
        elif ups_data['batt']['type_text'] == 'LiFePO4':
            ups_data['batt']['soc'] = int(((ups_data['batt']['v']-2.9)/0.7)*100)
        else:
            ups_data['batt']['soc'] = int(((ups_data['batt']['v']-3.4)/0.899)*100)

        # As SoC is a guess, check if we've got useless data or not
        if ups_data['batt']['soc'] > 100:
            ups_data['batt']['soc'] = 100
        elif ups_data['batt']['soc'] < 0:
            ups_data['batt']['soc'] = 0

        # check_ups_status()

    except Exception as e:
        logger.warn('Failed to get UPS data: ' + str(e))



# This will run if this file is run directly, sets up and services the pulsetrain.
# This should be done at boot, and separately from the rest of the control panel
# Ideally should be daemonized on control panel start such that it persists
# over panel restarts, and the panel checks if it's already running before trying
#  to start it. But for now, it can just be started in a 'screen -dm' session.

def main():
    logger.info('Setting up UPS pulsetrain')
    setup_pulsetrain()
    while True:
        sleep(5)

if __name__ == '__main__':
    main()
