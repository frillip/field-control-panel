from aiohttp import web
import megaio

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
		web.get('/fence_status', fence_status),
		web.get('/cameras_status', cameras_status),
		web.get('/lighting_status', lighting_status)])

web.run_app(app)
