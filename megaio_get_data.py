import megaio
from datetime import datetime
import global_vars
import logging
import colorlog

handler = colorlog.StreamHandler()
handler.setFormatter(global_vars.log_format)
logger = colorlog.getLogger(__name__)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Megaio boards can have different stack IDs (0-3), ours is 0.
megaio_stack_id = 0

# Bit mask dict for reading individual relays
relay_mask = { 1 : 0x01,
               2 : 0x02,
               3 : 0x04,
               4 : 0x08,
               5 : 0x10,
               6 : 0x20,
               7 : 0x40,
               8 : 0x80 }

# Function that gets ALL the relay states
def get_relay_data():

    try:
        # For some reason, you can only read ALL of the relay states as a single byte, so do this
        relay_byte=megaio.get_relays(megaio_stack_id)
        # Then for each relay
        for relay_id in global_vars.relay_data:
            # And if it's enabled
            if global_vars.relay_data[relay_id]['enabled']:
                # Bitmask it to get the raw state
                global_vars.relay_data[relay_id]['raw_state'] = bool(relay_byte & relay_mask[relay_id])
                # And invert to get the 'true' state if required
                global_vars.relay_data[relay_id]['state'] = global_vars.relay_data[relay_id]['raw_state'] ^ global_vars.relay_data[relay_id]['invert']

    except Exception as e:
        # Error has occurred, log it
        logger.error("Relay data task failed: " + str(e))

    pass

"""
# These don't do anything any more!
def get_batt_data():
    global megaio_stack_id
    batt_data = {}
    batt_v_adc_channel = 1
    batt_v_adc_scale = 11.05 # r47k + r4k7 + z3v3 + c10n
    batt_v_adc_offset = 0.0  # no offset!

    batt_c_adc_channel = 2
    batt_c_adc_scale = 14.7 # r2k2 + r4k7 + z3v3 + c10n  10A/V
    batt_c_adc_offset = 25.0 # ACS712 has a 25A (2.5V) offset

    try:
        batt_v_adc_volt=megaio.get_adc_volt(megaio_stack_id, batt_v_adc_channel)
        batt_v = (batt_v_adc_volt * batt_v_adc_scale) - batt_v_adc_offset 
        batt_data['v'] = round(batt_v,2)
        batt_c_adc_volt=megaio.get_adc_volt(megaio_stack_id, batt_c_adc_channel)
        batt_c = (batt_c_adc_volt * batt_c_adc_scale) - batt_c_adc_offset
        batt_data['c'] = round(batt_c,2)
        batt_data['e'] = False
    except:
        batt_data['e'] = True
    return batt_data

def get_pv_data():
    global megaio_stack_id
    pv_data = {}
    pv_v_adc_channel = 3
    pv_v_adc_scale = 11.05 # r47k + r4k7 + z3v3 + c10n
    pv_v_adc_offset = 0.0 # no offset!

    pv_c_adc_channel = 4
    pv_c_adc_scale = 14.7 # r2k2 + r4k7 + z3v3 + c10n  10A/V
    pv_c_adc_offset = 25.0  # ACS712 has a 25A (2.5V) offset

    try:
        pv_v_adc_volt=megaio.get_adc_volt(megaio_stack_id, pv_v_adc_channel)
        pv_v = (pv_v_adc_volt * pv_v_adc_scale) - pv_v_adc_scale
        pv_data['v'] = round(pv_v,2)
        pv_c_adc_volt=megaio.get_adc_volt(megaio_stack_id, pv_c_adc_channel)
        pv_c = (pv_c_adc_volt * pv_c_adc_scale) - pv_c_adc_offset
        pv_data['c'] = round(pv_c,2)
        pv_data['e'] = False
    except:
        pv_data['e'] = True
    return pv_data
"""
