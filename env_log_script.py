import requests
from requests.auth import HTTPBasicAuth
import json
import time
import datetime

url = "https://sheep.frillip.net/panel/status.json"
username = 
password = 

output_file = 

r = requests.get(url,
                 auth=HTTPBasicAuth(username,password))

unix_time_int = int(time.time())
utc_offset_sec = time.altzone if time.localtime().tm_isdst else time.timezone
utc_offset = datetime.timedelta(seconds=-utc_offset_sec)
iso8601_stamp = datetime.datetime.fromtimestamp(unix_time_int).replace(microsecond=0,tzinfo=datetime.timezone(offset=utc_offset)).isoformat()

human_date = datetime.datetime.fromtimestamp(unix_time_int).strftime("%d/%m/%Y")
human_time = datetime.datetime.fromtimestamp(unix_time_int).strftime("%H:%M:%S")

status_resp = r.json()
bme = status_resp["sensors"]["bme280"]
mppt = status_resp["mppt"]
bmv = status_resp["bmv"]
load = mppt["load"]
pv = mppt["pv"]
batt = bmv["batt"]
# This is useless because of rounding by the MPPT
# mppt_efficiency = round(( load["p"] / ( pv["p"] - batt["p"] ) ) * 100,2)
modem = status_resp["modem"]
data_usage = modem["data_usage"]
river = status_resp["river"]

f=open(output_file,"a")
print(unix_time_int,human_date,human_time,iso8601_stamp,
      bme['t'],bme['p'],bme['h'],
      load["v"],load["i"],load["p"],
      pv["v"],pv["i"],pv["p"],pv["yield"],
      batt["v"],batt["i"],batt["p"],batt["soc"],mppt["batt"]["cs"],batt["charge_consumed"],
      modem["connected_time"],data_usage["data_up"],data_usage["data_down"],
      modem["connected_total_time"],data_usage["data_total_up"],data_usage["data_total_down"],
      river["level"],
      sep=",", file=f)
f.close()
