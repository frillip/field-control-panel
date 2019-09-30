import megaio
megaio_stack_id = 0

def get_relay_data():
    global megaio_stack_id
    relay_data = {}
    try:
        relay_byte=megaio.get_relays(megaio_stack_id)

        relay_1_data = {}
        relay_1_data['name'] = "fence"
        relay_1_data
        relay_1_data['real_state'] = bool(relay_byte & 0x01)
        relay_1_data['invert'] = True
        relay_1_data['state'] = relay_1_data['real_state'] ^ relay_1_data['invert']
        relay_data['1'] = relay_1_data

        relay_2_data = {}
        relay_2_data['name'] = "cameras"
        relay_2_data['real_state'] = bool(relay_byte & 0x02)
        relay_2_data['invert'] = False
        relay_2_data['state'] = relay_2_data['real_state'] ^ relay_2_data['invert']
        relay_data['2'] = relay_2_data

        relay_3_data = {}
        relay_3_data['name'] = "lighting"
        relay_3_data['real_state'] = bool(relay_byte & 0x04)
        relay_3_data['invert'] = False
        relay_3_data['state'] = relay_3_data['real_state'] ^ relay_3_data['invert']
        relay_data['3'] = relay_3_data

        relay_data['e'] = False

    except:
        relay_data['e'] = True

    return relay_data

def get_batt_data():
    global megaio_stack_id
    batt_data = {}
    batt_v_adc_channel = 3
    batt_v_adc_scale = 0.4
    batt_c_adc_channel = 4
    batt_c_adc_scale = 0.1
    try:
        batt_v_adc_volt=megaio.get_adc_volt(megaio_stack_id, batt_v_adc_channel)
        batt_v = batt_v_adc_volt * batt_v_adc_scale
        batt_data['v'] = round(batt_v,2)
        batt_c_adc_volt=megaio.get_adc_volt(megaio_stack_id, batt_c_adc_channel)
        batt_c = batt_c_adc_volt * batt_c_adc_scale
        batt_data['c'] = round(batt_c,2)
        batt_data['e'] = False
    except:
        batt_data['e'] = True
    return batt_data

def get_pv_data():
    global megaio_stack_id
    pv_data = {}
    pv_v_adc_channel = 3
    pv_v_adc_scale = 0.2
    pv_c_adc_channel = 4
    pv_c_adc_scale = 0.1
    try:
        pv_v_adc_volt=megaio.get_adc_volt(megaio_stack_id, pv_v_adc_channel)
        pv_v = pv_v_adc_volt * pv_v_adc_scale
        pv_data['v'] = round(pv_v,2)
        pv_c_adc_volt=megaio.get_adc_volt(megaio_stack_id, pv_c_adc_channel)
        pv_c = pv_c_adc_volt * pv_c_adc_scale
        pv_data['c'] = round(pv_c,2)
        pv_data['e'] = False
    except:
        pv_data['e'] = True
    return pv_data
