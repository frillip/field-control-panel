import megaio
megaio_stack_id = 0

def set_relay_state(request):
    global megaio_stack_id

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

    if "fence" in request:
        if request['fence'] == "off":
            megaio.set_relay(megaio_stack_id,fence_relay,fence_off_value)
            return "Fence now OFF"
        elif request['fence'] == "on":
            megaio.set_relay(megaio_stack_id,fence_relay,fence_on_value)
            return "Fence now ON"
    if "cameras" in request:
        if request['cameras'] == "off":
            megaio.set_relay(megaio_stack_id,cameras_relay,cameras_off_value)
            return "Cameras now OFF"
        elif request['cameras'] == "on":
            megaio.set_relay(megaio_stack_id,cameras_relay,cameras_on_value)
            return "Cameras now ON"
    if "lighting" in request:
        if request['lighting'] == "off":
            megaio.set_relay(megaio_stack_id,lighting_relay,lighting_off_value)
            return "Lighting now OFF"
        elif request['lighting'] == "on":
            megaio.set_relay(megaio_stack_id,lighting_relay,lighting_on_value)
            return "Lighting now ON"
    return "I don't know what you want from me"
