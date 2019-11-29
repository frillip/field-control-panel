from datetime import datetime
from colorlog import ColoredFormatter

log_format = ColoredFormatter(
        "%(asctime)s %(log_color)s[%(levelname)s]%(reset)s %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
        log_colors={
        'DEBUG': 'cyan',
        'INFO': 'green',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'red,bg_white',
        })

bme_data = {}
mppt_data = {}
mppt_data["batt"] = {}
mppt_data["load"] = {}
mppt_data["pv"] = {}

modem_data = {}
river_data = {}

relay_map = { "fence" : 1 , "cameras" : 2, "lighting" : 3 }

relay_timeout = { 1 : 0 , 2: 0 , 3 : 0}
relay_timestamp = { 1 : 0 , 2: 0 , 3 : 0}

relay_data = {}

relay_data[1] = {}
relay_data[1]['name'] = "fence"
relay_data[1]['raw_state'] = False
relay_data[1]['invert'] = True
relay_data[1]['state'] = relay_data[1]['raw_state'] ^ relay_data[1]['invert']
relay_data[1]['auto_on'] = False
relay_data[1]['auto_off'] = False
relay_data[1]['auto_timeout'] = 0
relay_data[1]['last_state_change'] = datetime.now().replace(microsecond=0).isoformat()

relay_data[2] = {}
relay_data[2]['name'] = "cameras"
relay_data[2]['raw_state'] = False
relay_data[2]['invert'] = False
relay_data[2]['state'] = relay_data[2]['raw_state'] ^ relay_data[2]['invert']
relay_data[2]['auto_on'] = False
relay_data[2]['auto_off'] = True
relay_data[2]['auto_timeout'] = 300
relay_data[2]['last_state_change'] = datetime.now().replace(microsecond=0).isoformat()

relay_data[3] = {}
relay_data[3]['name'] = "lighting"
relay_data[3]['raw_state'] = False
relay_data[3]['invert'] = False
relay_data[3]['state'] = relay_data[3]['raw_state'] ^ relay_data[3]['invert']
relay_data[3]['auto_on'] = False
relay_data[3]['auto_off'] = False
relay_data[3]['auto_timeout'] = 0
relay_data[3]['last_state_change'] = datetime.now().replace(microsecond=0).isoformat()
