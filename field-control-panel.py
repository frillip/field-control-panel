from aiohttp import web
import json
from bme_env_data import get_bme_data
from megaio_get_data import get_relay_data,get_batt_data,get_pv_data
from megaio_set_relays import set_relay_state
from e3372_interface import get_modem_data

async def indexresp(request):
    return web.FileResponse('./static/index.html')

async def buttonhandler(request):
    data = await request.post()
    resp=set_relay_state(data)
    return web.Response(text=resp)

async def status_json(request):
    status_data = {}
    status_data['relay'] = get_relay_data()
    status_data['bme'] = get_bme_data()
    status_data['batt'] = get_batt_data()
    status_data['pv'] = get_pv_data()
    status_data['modem'] = get_modem_data()
    resp_json = json.dumps(status_data)
    return web.Response(text=resp_json,content_type='application/json')

async def bme_json(request):
    resp_json = json.dumps(get_bme_data())
    return web.Response(text=resp_json,content_type='application/json')

async def relay_json(request):
    resp_json = json.dumps(get_relay_data())
    return web.Response(text=resp_json,content_type='application/json')

async def batt_json(request):
    resp_json = json.dumps(get_batt_data())
    return web.Response(text=resp_json,content_type='application/json')

async def pv_json(request):
    resp_json = json.dumps(get_pv_data())
    return web.Response(text=resp_json,content_type='application/json')

async def modem_json(request):
    resp_json = json.dumps(get_modem_data())
    return web.Response(text=resp_json,content_type='application/json')

app = web.Application()
app.add_routes([web.get('/', indexresp),
		web.post('/', buttonhandler),
                web.get('/status.json', status_json),
                web.get('/relay.json', relay_json),
                web.get('/bme.json', bme_json),
		web.get('/batt.json', batt_json),
		web.get('/pv.json', pv_json),
		web.get('/modem.json', modem_json)])
web.run_app(app)
