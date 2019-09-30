import smbus2
import bme280

bme_port = 1 # Yes
bme_address = 0x76 # Cheap BME280s are 0x76, Adafruit is 0x77
bme_bus = smbus2.SMBus(bme_port)

bme280.load_calibration_params(bme_bus,bme_address)

def get_environment_data():
    global bme_bus
    global bme_address
    bme_data = {}
    print("Getting BME data... ",end = '')
    try:
        bme_raw_data = bme280.sample(bme_bus,bme_address)
        print("Success!")
        bme_data['h'] = round(bme_raw_data.humidity,1)
        bme_data['p'] = round(bme_raw_data.pressure)
        bme_data['t'] = round(bme_raw_data.temperature,1)
        bme_data['e'] = False
    except:
        print("Fail!")
        bme_data['h'] = 0
        bme_data['p'] = 0
        bme_data['t'] = 0
        bme_data['e'] = True
    return bme_data
#    bme_json = json.dumps(bme_data)
#    return bme_json
