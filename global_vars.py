bme_data = {}
mppt_data = {}
modem_data = {}

relay_map = { "fence" : 1 , "cameras" : , "lighting" : 3 }

relay_timeout = { 1 : 0 , 2: 0 , 3 : 0}

relay_data = {}

# Somewhat unnecessary assignments but whatever

relay_1_data = {}
relay_1_data['name'] = "fence"
relay_1_data['raw_state'] = False
relay_1_data['invert'] = True
relay_1_data['state'] = relay_1_data['raw_state'] ^ relay_1_data['invert']
relay_1_data['auto_on'] = False
relay_1_data['auto_off'] = False
relay_1_data['auto_timeout'] = 0
relay_1_data['last_state_change'] = datetime.now().replace(microsecond=0).isoformat()
relay_data[1] = relay_1_data

relay_2_data = {}
relay_2_data['name'] = "cameras"
relay_2_data['raw_state'] = False
relay_2_data['invert'] = False
relay_2_data['state'] = relay_2_data['raw_state'] ^ relay_2_data['invert']
relay_2_data['auto_on'] = False
relay_2_data['auto_off'] = True
relay_2_data['auto_timeout'] = 120
relay_2_data['last_state_change'] = datetime.now().replace(microsecond=0).isoformat()
relay_data[2] = relay_2_data

relay_3_data = {}
relay_3_data['name'] = "lighting"
relay_3_data['raw_state'] = False
relay_3_data['invert'] = False
relay_3_data['state'] = relay_3_data['raw_state'] ^ relay_3_data['invert']
relay_3_data['auto_on'] = False
relay_3_data['auto_off'] = False
relay_3_data['auto_timeout'] = 0
relay_3_data['last_state_change'] = datetime.now().replace(microsecond=0).isoformat()
relay_data[3] = relay_3_data
