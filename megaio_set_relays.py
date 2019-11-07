import megaio
from datetime import datetime
import global_vars

megaio_stack_id = 0
fence_relay = 1
cameras_relay = 2
lighting_relay = 3

def set_relay_state(request):
    global megaio_stack_id

    global fence_relay
    fence_off_value = 1
    fence_on_value = 0
    fence_relay_mask = 0x01 << (fence_relay - 1)

    global cameras_relay
    cameras_off_value = 0
    cameras_on_value = 1
    cameras_relay_mask = 0x01 << (cameras_relay - 1)

    global lighting_relay
    lighting_off_value = 0
    lighting_on_value = 1
    lighting_relay_mask = 0x01 << (lighting_relay - 1)

    now_iso_stamp = datetime.now().replace(microsecond=0).isoformat()

    if "fence" in request:
        if request['fence'] == "off":
            megaio.set_relay(megaio_stack_id,fence_relay,fence_off_value)
            global_vars.relay_data[fence_relay]['last_state_change'] = now_iso_stamp
            return "Fence now OFF"
        elif request['fence'] == "on":
            megaio.set_relay(megaio_stack_id,fence_relay,fence_on_value)
            global_vars.relay_data[fence_relay]['last_state_change'] = now_iso_stamp
            return "Fence now ON"
    if "cameras" in request:
        if request['cameras'] == "off":
            megaio.set_relay(megaio_stack_id,cameras_relay,cameras_off_value)
            global_vars.relay_data[cameras_relay]['last_state_change'] = now_iso_stamp
            return "Cameras now OFF"
        elif request['cameras'] == "on":
            megaio.set_relay(megaio_stack_id,cameras_relay,cameras_on_value)
            global_vars.relay_data[cameras_relay]['last_state_change'] = now_iso_stamp
            return "Cameras now ON"
    if "lighting" in request:
        if request['lighting'] == "off":
            megaio.set_relay(megaio_stack_id,lighting_relay,lighting_off_value)
            global_vars.relay_data[lighting_relay]['last_state_change'] = now_iso_stamp
            return "Lighting now OFF"
        elif request['lighting'] == "on":
            megaio.set_relay(megaio_stack_id,lighting_relay,lighting_on_value)
            global_vars.relay_data[lighting_relay]['last_state_change'] = now_iso_stamp
            return "Lighting now ON"
    return "I don't know what you want from me"

def relay_auto_timeout():

    global megaio_stack_id

    global fence_relay
    global cameras_relay
    global lighting_relay

    now = datetime.now()
    now_iso_stamp = datetime.now().replace(microsecond=0).isoformat()
    now_unix = (now - datetime(1970, 1, 1)).total_seconds()

    fence_relay_data = global_vars.relay_data[fence_relay]
    last_change = datetime.strptime(fence_relay_data['last_state_change'], '%Y-%m-%dT%H:%M:%S')
    last_change_unix = (last_change - datetime(1970, 1, 1)).total_seconds()
    if fence_relay_data['auto_timeout'] and last_change_unix + fence_relay_data['auto_timeout'] < now_unix:
        if fence_relay_data['auto_off'] and fence_relay_data['state']:
            print("Automatically turning fence off")
            new_raw_state = False ^ fence_relay_data['invert']
            megaio.set_relay(megaio_stack_id,fence_relay,new_raw_state)
            global_vars.relay_data[fence_relay]['last_state_change'] = now_iso_stamp
        if fence_relay_data['auto_on'] and not fence_relay_data['state']:
            print("Automatically turning fence on")
            new_raw_state = True ^ fence_relay_data['invert']
            megaio.set_relay(megaio_stack_id,fence_relay,new_raw_state)
            global_vars.relay_data[fence_relay]['last_state_change'] = now_iso_stamp

    cameras_relay_data = global_vars.relay_data[cameras_relay]
    last_change = datetime.strptime(cameras_relay_data['last_state_change'], '%Y-%m-%dT%H:%M:%S')
    last_change_unix = (last_change - datetime(1970, 1, 1)).total_seconds()
    if cameras_relay_data['auto_timeout'] and last_change_unix + cameras_relay_data['auto_timeout'] < now_unix:
        if cameras_relay_data['auto_off'] and cameras_relay_data['state']:
            print("Automatically turning cameras off")
            new_raw_state = False ^ cameras_relay_data['invert']
            megaio.set_relay(megaio_stack_id,cameras_relay,new_raw_state)
            global_vars.relay_data[cameras_relay]['last_state_change'] = now_iso_stamp
        if cameras_relay_data['auto_on'] and not cameras_relay_data['state']:
            print("Automatically turning cameras on")
            new_raw_state = True ^ cameras_relay_data['invert']
            megaio.set_relay(megaio_stack_id,cameras_relay,new_raw_state)
            global_vars.relay_data[cameras_relay]['last_state_change'] = now_iso_stamp

    lighting_relay_data = global_vars.relay_data[lighting_relay]
    last_change = datetime.strptime(lighting_relay_data['last_state_change'], '%Y-%m-%dT%H:%M:%S')
    last_change_unix = (last_change - datetime(1970, 1, 1)).total_seconds()
    if lighting_relay_data['auto_timeout'] and last_change_unix + lighting_relay_data['auto_timeout'] < now_unix:
        if lighting_relay_data['auto_off'] and lighting_relay_data['state']:
            print("Automatically turning lighting off")
            new_raw_state = False ^ lighting_relay_data['invert']
            megaio.set_relay(megaio_stack_id,lighting_relay,new_raw_state)
            global_vars.relay_data[lighting_relay]['last_state_change'] = now_iso_stamp
        if lighting_relay_data['auto_on'] and not lighting_relay_data['state']:
            print("Automatically turning lighting on")
            new_raw_state = True ^ lighting_relay_data['invert']
            megaio.set_relay(megaio_stack_id,lighting_relay,new_raw_state)
            global_vars.relay_data[lighting_relay]['last_state_change'] = now_iso_stamp
