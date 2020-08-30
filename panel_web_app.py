import asyncio
from time import sleep
from aiohttp import web
import json
from relays import relay_handle_request,generate_relay_json
from system_status import maintenance_handle_request,system_state,get_log_tail
import global_vars
from sensors import bme280_data,tsl2561_data,lis3dh_data,ina260,gps_data
from environment_agency import river_data
from weather import weather_data
from sun import sun_data
from pico_ups import ups_data
from yaml_config import config
import logging
import colorlog

logger = colorlog.getLogger(__name__)
logger.addHandler(global_vars.file_handler)
logger.addHandler(global_vars.handler)
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

    async def styleresp(request):
        return web.FileResponse('./webroot/style.css')

    async def canaryresp(request):
        return web.Response(text=config['remote']['canary_string'])

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
        resp=relay_handle_request(relay_req)
        return web.Response(text=resp)

    async def maintenancetoggle(request):
        logger.info("Maintenance mode state change requested")
        data = await request.text()
        maintenance_req=json.loads(data)
        resp=maintenance_handle_request(maintenance_req)
        return web.Response(text=resp)

    async def status_json(request):
        status_data = {}
        status_data['relay'] = generate_relay_json()
        sensors_data = {}
        sensors_data['bme280'] = bme280_data
        sensors_data['tsl2561'] = tsl2561_data
        sensors_data['lis3dh'] = lis3dh_data
        sensors_data['ina260'] = ina260_data
        sensors_data['gps'] = gps_data
        status_data['sensors'] = sensors_data
        status_data['mppt'] = global_vars.mppt_data
        status_data['bmv'] = global_vars.bmv_data
        status_data['modem'] = global_vars.modem_data
        status_data['river'] = river_data
        status_data['sun'] = sun_data
        status_data['system'] = system_state
        status_data['ups'] = ups_data
        status_data['weather'] = weather_data
        return web.json_response(status_data)

    async def relay_json(request):
        return web.json_response(generate_relay_json())

    async def bme280_json(request):
        return web.json_response(bme280_data)

    async def tsl2561_json(request):
        return web.json_response(tsl2561_data)

    async def lis3dh_json(request):
        return web.json_response(lis3dh_data)

    async def ina260_json(request):
        return web.json_response(ina260_data)

    async def gps_json(request):
        return web.json_response(gps_data)

    async def sensors_json(request):
        sensors_data = {}
        sensors_data['bme280'] = bme280_data
        sensors_data['tsl2561'] = tsl2561_data
        sensors_data['lis3dh'] = lis3dh_data
        sensors_data['ina260'] = ina260_data
        sensors_data['gps'] = gps_data
        return web.json_response(sensors_data)

    async def mppt_json(request):
        return web.json_response(global_vars.mppt_data)

    async def bmv_json(request):
        return web.json_response(global_vars.bmv_data)

    async def modem_json(request):
        return web.json_response(global_vars.modem_data)

    async def river_json(request):
        return web.json_response(river_data)

    async def log_json(request):
        log  = get_log_tail(50)
        return web.json_response(log)

    async def system_json(request):
        return web.json_response(system_state)

    async def sun_json(request):
        return web.json_response(sun_data)

    async def ups_json(request):
        return web.json_response(ups_data)

    async def weather_json(request):
        return web.json_response(weather_data)

    app = web.Application()
    app.add_routes([web.get('/', indexresp),
                    web.get('/main.js', scriptresp),
                    web.get('/style.css', styleresp),
                    web.get('/'+config['remote']['canary_url'], canaryresp),
                    web.get('/stats_ajax.json', stats_ajax_get),
                    web.post('/buttons', buttonhandler),
                    web.post('/maintenance', maintenancetoggle),
                    web.get('/status.json', status_json),
                    web.get('/relay.json', relay_json),
                    web.get('/bme280.json', bme280_json),
                    web.get('/tsl2561.json', tsl2561_json),
                    web.get('/lis3dh.json', lis3dh_json),
                    web.get('/ina260.json', ina260_json),
                    web.get('/gps.json', gps_json),
                    web.get('/sensors.json', sensors_json),
                    web.get('/mppt.json', mppt_json),
                    web.get('/bmv.json', bmv_json),
                    web.get('/modem.json', modem_json),
                    web.get('/river.json', river_json),
                    web.get('/sun.json', sun_json),
                    web.get('/system.json', system_json),
                    web.get('/log.json', log_json),
                    web.get('/ups.json', ups_json),
                    web.get('/weather.json', weather_json)])
    runner = web.AppRunner(app, access_log=None)
    return runner
