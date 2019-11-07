import megaio
from datetime import datetime
import global_vars
megaio_stack_id = 0

def get_relay_data():
    global megaio_stack_id

    relay_data = {}
    try:
        relay_byte=megaio.get_relays(megaio_stack_id)

        relay_1_data = {}
        relay_1_data['name'] = "fence"
        relay_1_data['raw_state'] = bool(relay_byte & 0x01)
        relay_1_data['invert'] = True
        relay_1_data['state'] = relay_1_data['raw_state'] ^ relay_1_data['invert']
        relay_1_data['auto_on'] = False
        relay_1_data['auto_off'] = False
        relay_1_data['auto_timeout'] = 0
        try:
            relay_1_data['last_state_change'] = global_vars.relay_data[1]['last_state_change']
        except:
            relay_1_data['last_state_change'] = datetime.now().replace(microsecond=0).isoformat()
        relay_data[1] = relay_1_data

        relay_2_data = {}
        relay_2_data['name'] = "cameras"
        relay_2_data['raw_state'] = bool(relay_byte & 0x02)
        relay_2_data['invert'] = False
        relay_2_data['state'] = relay_2_data['raw_state'] ^ relay_2_data['invert']
        relay_2_data['auto_on'] = False
        relay_2_data['auto_off'] = True
        relay_2_data['auto_timeout'] = 120
        try:
            relay_2_data['last_state_change'] = global_vars.relay_data[2]['last_state_change']
        except:
            relay_2_data['last_state_change'] = datetime.now().replace(microsecond=0).isoformat()
        relay_data[2] = relay_2_data

        relay_3_data = {}
        relay_3_data['name'] = "lighting"
        relay_3_data['raw_state'] = bool(relay_byte & 0x04)
        relay_3_data['invert'] = False
        relay_3_data['state'] = relay_3_data['raw_state'] ^ relay_3_data['invert']
        relay_3_data['auto_on'] = False
        relay_3_data['auto_off'] = False
        relay_3_data['auto_timeout'] = 0
        try:
            relay_3_data['last_state_change'] = global_vars.relay_data[3]['last_state_change']
        except:
            relay_3_data['last_state_change'] = datetime.now().replace(microsecond=0).isoformat()
        relay_data[3] = relay_3_data

        relay_data['e'] = False

    except:
        relay_data['e'] = True

    global_vars.relay_data = relay_data

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
