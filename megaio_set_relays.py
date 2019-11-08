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
            global_vars.relay_timeout[fence_relay] = global_vars.relay_data[fence_relay]['auto_timeout']
            return "Fence now OFF"
        elif request['fence'] == "on":
            megaio.set_relay(megaio_stack_id,fence_relay,fence_on_value)
            global_vars.relay_data[fence_relay]['last_state_change'] = now_iso_stamp
            global_vars.relay_timeout[fence_relay] = global_vars.relay_data[fence_relay]['auto_timeout']
            return "Fence now ON"

    if "cameras" in request:
        if request['cameras'] == "off":
            megaio.set_relay(megaio_stack_id,cameras_relay,cameras_off_value)
            global_vars.relay_data[cameras_relay]['last_state_change'] = now_iso_stamp
            global_vars.relay_timeout[cameras_relay] = global_vars.relay_data[cameras_relay]['auto_timeout']
            return "Cameras now OFF"
        elif request['cameras'] == "on":
            megaio.set_relay(megaio_stack_id,cameras_relay,cameras_on_value)
            global_vars.relay_data[cameras_relay]['last_state_change'] = now_iso_stamp
            global_vars.relay_timeout[cameras_relay] = global_vars.relay_data[cameras_relay]['auto_timeout']
            return "Cameras now ON"

    if "lighting" in request:
        if request['lighting'] == "off":
            megaio.set_relay(megaio_stack_id,lighting_relay,lighting_off_value)
            global_vars.relay_data[lighting_relay]['last_state_change'] = now_iso_stamp
            global_vars.relay_timeout[lighting_relay] = global_vars.relay_data[lighting_relay]['auto_timeout']
            return "Lighting now OFF"
        elif request['lighting'] == "on":
            megaio.set_relay(megaio_stack_id,lighting_relay,lighting_on_value)
            global_vars.relay_data[lighting_relay]['last_state_change'] = now_iso_stamp
            global_vars.relay_timeout[lighting_relay] = global_vars.relay_data[lighting_relay]['auto_timeout']
            return "Lighting now ON"
    return "I don't know what you want from me"

def relay_auto_timeout():

    global megaio_stack_id

    now_iso_stamp = datetime.now().replace(microsecond=0).isoformat()

    for relay in range(1,4):
        try:
            if global_vars.relay_timeout[relay]:
                global_vars.relay_timeout[relay] -= 1
        except:
            global_vars.relay_timeout[relay] = 0

        if global_vars.relay_data[relay]['auto_timeout'] and not global_vars.relay_timeout[relay]:

            if global_vars.relay_data[relay]['auto_off'] and global_vars.relay_data[relay]['state']:
                print("Automatically turning " + global_vars.relay_data[relay]['name'] + " off")
                new_raw_state = False ^ global_vars.relay_data[relay]['invert']
                megaio.set_relay(megaio_stack_id,relay,new_raw_state)
                global_vars.relay_data[relay]['last_state_change'] = now_iso_stamp

            if global_vars.relay_data[relay]['auto_on'] and not global_vars.relay_data[relay]['state']:
                print("Automatically turning " + global_vars.relay_data[relay]['name'] + " on")
                new_raw_state = True ^ global_vars.relay_data[relay]['invert']
                megaio.set_relay(megaio_stack_id,relay,new_raw_state)
                global_vars.relay_data[relay]['last_state_change'] = now_iso_stamp
