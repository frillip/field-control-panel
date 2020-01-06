import asyncio
from time import sleep
from aiohttp import web
import json
from megaio_set_relays import set_relay_state
import global_vars
import logging
import colorlog

handler = colorlog.StreamHandler()
handler.setFormatter(global_vars.log_format)
logger = colorlog.getLogger(__name__)
logger.addHandler(handler)
logger.setLevel(global_vars.log_level)

run_webapp_server = True

loop = asyncio.new_event_loop()

def stop_server():
    loop.call_soon_threadsafe(loop.stop)
    while loop.is_running():
        logger.info("Webapp still running")
        sleep(1)
    loop.close()
    logger.warning("Webapp server stopped")

def run_server(runner):
    try:
        asyncio.set_event_loop(loop)
        loop.run_until_complete(runner.setup())
        logger.info("Starting webapp server")
        site = web.TCPSite(runner, 'localhost', 8080)
        loop.run_until_complete(site.start())
        loop.run_forever()
    except Exception as e:
        logger.error("Webapp server failed: " + str(e))

def run_web_app():
    async def indexresp(request):
        return web.FileResponse('./webroot/index.html')

    async def scriptresp(request):
        return web.FileResponse('./webroot/main.js')

    async def stats_ajax_get(request):
        ajax_resp = {}
        ajax_resp['bv'] = global_vars.bmv_data['batt']['v']
        ajax_resp['bi'] = global_vars.bmv_data['batt']['i']
        ajax_resp['bsoc'] = global_vars.bmv_data['batt']['soc']
        ajax_resp['bcs'] = global_vars.mppt_data['batt']['cs_text']
        ajax_resp['pvp'] = global_vars.mppt_data['pv']['p']
        ajax_resp['pvv'] = global_vars.mppt_data['pv']['v']
        ajax_resp['pvmppt'] = global_vars.mppt_data['pv']['mppt_text']
        ajax_resp['pvy'] = global_vars.mppt_data['pv']['yield']
        return web.json_response(ajax_resp)

    async def buttonhandler(request):
        logger.info("Relay state change requested")
        data = await request.text()
        relay_req=json.loads(data)
        resp=set_relay_state(relay_req)
        return web.Response(text=resp)

    async def status_json(request):
        status_data = {}
        status_data['relay'] = global_vars.relay_data
        status_data['bme'] = global_vars.bme_data
        status_data['mppt'] = global_vars.mppt_data
        status_data['bmv'] = global_vars.bmv_data
        status_data['modem'] = global_vars.modem_data
        status_data['river'] = global_vars.river_data
        status_data['sun'] = global_vars.sun_data
        status_data['weather'] = global_vars.weather_data
        return web.json_response(status_data)

    async def relay_json(request):
        return web.json_response(global_vars.relay_data)

    async def bme_json(request):
        return web.json_response(global_vars.bme_data)

    async def mppt_json(request):
        return web.json_response(global_vars.mppt_data)

    async def bmv_json(request):
        return web.json_response(global_vars.bmv_data)

    async def modem_json(request):
        return web.json_response(global_vars.modem_data)

    async def river_json(request):
        return web.json_response(global_vars.river_data)

    async def sun_json(request):
        return web.json_response(global_vars.sun_data)

    async def weather_json(request):
        return web.json_response(global_vars.weather_data)

    app = web.Application()
    app.add_routes([web.get('/', indexresp),
                    web.get('/main.js', scriptresp),
                    web.get('/stats_ajax.json', stats_ajax_get),
                    web.post('/buttons', buttonhandler),
                    web.get('/status.json', status_json),
                    web.get('/relay.json', relay_json),
                    web.get('/bme.json', bme_json),
                    web.get('/mppt.json', mppt_json),
                    web.get('/bmv.json', bmv_json),
                    web.get('/modem.json', modem_json),
                    web.get('/river.json', river_json),
                    web.get('/sun.json', sun_json),
                    web.get('/weather.json', weather_json)])
    runner = web.AppRunner(app, access_log=None)
    return runner
