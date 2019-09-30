from aiohttp import web
import megaio
import bme280
import smbus2
import json

bme_port = 1 # Yes
bme_address = 0x76 # Cheap BME280s are 0x76, Adafruit is 0x77
bme_bus = smbus2.SMBus(bme_port)

bme280.load_calibration_params(bme_bus,bme_address)

def get_environment_json():
    global bme_bus
    global bme_address
    bme_json_data = {}
    print("Getting BME data... ",end = '')
    try:
        bme280_data = bme280.sample(bme_bus,bme_address)
        print("Success!")
        bme_json_data['h'] = round(bme280_data.humidity,1)
        bme_json_data['p'] = round(bme280_data.pressure)
        bme_json_data['t'] = round(bme280_data.temperature,1)
        bme_json_data['e'] = False
    except:
        print("Fail!")
        bme_json_data['h'] = 0
        bme_json_data['p'] = 0
        bme_json_data['t'] = 0
        bme_json_data['e'] = True
    bme_json = json.dumps(bme_json_data)
    return bme_json

megaio_stack_id = 0

fence_relay = 1
fence_off_value = 1
fence_on_value = 0
fence_relay_mask = 0x01 << (fence_relay - 1)

cameras_relay = 2
cameras_off_value = 0
cameras_on_value = 1
cameras_relay_mask = 0x01 << (cameras_relay - 1)

lighting_relay = 3
lighting_off_value = 0
lighting_on_value = 1
lighting_relay_mask = 0x01 << (lighting_relay - 1)

async def indexresp(request):
    return web.FileResponse('./index.html')

async def buttonhandler(request):
    data = await request.post()
    if "fence" in data:
        print("Fence yo")
        if data['fence'] == "off":
            print("Fence off")
            megaio.set_relay(megaio_stack_id,fence_relay,fence_off_value)
            return web.Response(text="Fence now OFF")
        elif data['fence'] == "on":
            print("Fence on")
            megaio.set_relay(megaio_stack_id,fence_relay,fence_on_value)
            return web.Response(text="Fence now ON")
    if "cameras" in data:
        print("Cameras yo")
        if data['cameras'] == "off":
            print("Cameras off")
            megaio.set_relay(megaio_stack_id,cameras_relay,cameras_off_value)
            return web.Response(text="Cameras now OFF")
        elif data['cameras'] == "on":
            print("Cameras on")
            megaio.set_relay(megaio_stack_id,cameras_relay,cameras_on_value)
            return web.Response(text="Cameras now ON")
    if "lighting" in data:
        print("lighting yo")
        if data['lighting'] == "off":
            print("lighting off")
            megaio.set_relay(megaio_stack_id,lighting_relay,lighting_off_value)
            return web.Response(text="Lighting now OFF")
        elif data['lighting'] == "on":
            print("lighting on")
            megaio.set_relay(megaio_stack_id,lighting_relay,lighting_on_value)
            return web.Response(text="Lighting now ON")
    return web.FileResponse('./index.html')

async def status_json(request):
    if megaio.get_relays(megaio_stack_id) & fence_relay_mask == fence_on_value:
        json_fence_status = True
    else:
        json_fence_status = False
    if megaio.get_relays(megaio_stack_id) & cameras_relay_mask == cameras_on_value:
        json_cameras_status = True
    else:
        json_cameras_status = False
    if megaio.get_relays(megaio_stack_id) & lighting_relay_mask == lighting_on_value:
        json_lighting_status = True
    else:
        json_lighting_status = False

async def bme_data(request):
    resp = get_environment_json()
    return web.Response(text=resp,content_type='application/json')

async def fence_status(request):
    if megaio.get_relays(megaio_stack_id) & fence_relay_mask == fence_on_value:
        fence_status_text="ON"
    else:
        fence_status_text="OFF"
    return web.Response(text=fence_status_text)

async def cameras_status(request):
    if megaio.get_relays(megaio_stack_id) & cameras_relay_mask == cameras_on_value:
        cameras_status_text="ON"
    else:
        cameras_status_text="OFF"
    return web.Response(text=cameras_status_text)

async def lighting_status(request):
    if megaio.get_relays(megaio_stack_id) & lighting_relay_mask == lighting_on_value:
        lighting_status_text="ON"
    else:
        lighting_status_text="OFF"
    return web.Response(text=lighting_status_text)

app = web.Application(debug=True)
app.add_routes([web.get('/', indexresp),
		web.post('/', buttonhandler),
                web.get('/bme.json', bme_data),
		web.get('/fence_status', fence_status),
		web.get('/cameras_status', cameras_status),
		web.get('/lighting_status', lighting_status)])

web.run_app(app)
