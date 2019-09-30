# Field Control Panel

Based on a Raspberry Pi 3 A, with a MegaIO hat. Goal is to have a web based interface to view and control various things on the field, eg, the electric fencing to the ~~velociraptor~~ horse/sheep paddocks, power supply to the IP cameras overseeing the ~~embryo storage fecility~~ field shelter, and exterior lighting around the ~~east dock~~ entrace gateway.

Eventually this will also be able to provide information such as battery voltage and current consumption, as well as information regarding the PV array and weather around ~~Isla Nublar~~ Blaby, UK.

## bme_env_data.py

Returns data from a BME280 in JSON format.

### get_bme_data
Returns temperature, pressure and humidiy data as JSON from the BME280.

## megaio_get_data.py

Returns data from the MegaIO hat.

### get_batt_data
Returns battery data, voltage input to adc1 and current on adc2 as JSON from the MegaIO hat. Has a sclaing factor for each.

### get_pv_data
Returns PV array data, voltage input to adc1 and current on adc2 as JSON from the MegaIO hat. Has a sclaing factor for each.

### get_relay_data
Returns a JSON object showing relay state, feature name, feature state across relays 1-3 on the MegaIO hat. How this get specified is up for debate as I can't think of a decent way of doing it yet. Must not fall into the trap of making it too generic.

## megaio_set_relays.py

Does things with the form data recieved from `static/index.html`. Need to think of a better way of handling this, see above.

## static/index.html

Literally just a page with buttons. Will ideally reflect current state of relays and show battery/pv/weather info. Historical data not required but might be nice over a 24h period.
