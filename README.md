# Field Control Panel

Based on a Raspberry Pi 4 B, with a MegaIO hat. Goal is to have a web based interface that automatically populates with useful information and the state of the various systems. Also used to control various things on the field, eg, the electric fencing to the ~~velociraptor~~ horse/sheep paddocks, power supply to the IP cameras overseeing the ~~embryo storage fecility~~ field shelter, and exterior lighting around the ~~east dock~~ entrace gateway.

Currently the control panel page is a static set of buttons and most useful data is outputted in JSON format.

## Scheduler

Most tasks are run off a scheduler, exceptions being the VE.Direct interface tasks as these are synchronous serial tasks, and the aiohttp web server.

## Web server

The main index page and JSON outputs are presented using the aiohttp web server on http://localhost:8080/ . This is proxied by apache running on the Pi which takes care of access control and HTTPS.

## Configuration

The majority of this is done in `global_vars.py` however some other specific bits are specified in their respective files (such as USB serial device for the VE.Direct interfaces). This needs moving to a YAML file or similar in the future perhaps, but for now it is fine where it is.

## Private user data

This lives in `user_data.py` which is ignored by git. Currently it contains phone numbers for alerts and API keys for the clickatell SMS gateway.

## VE.Direct interface

Currently there are functions to read information from Victron modules (currently a SmartSolar 100|20 and BMV-712) over VE.Direct USB interfaces. Currently this is via the human-readable VE.Direct protocol which is automatically output every second or so by the module. Ideally in the future this should be requested and read back using the Victron HEX protocol (see issue #48), or, even better, via Bluetooth (see issue #14), however the Bluetooth protocol is not opensourced like the HEX protocol. This would also allow control of the modules.

There are also functions to check the overall health of the system, but these are relatively simplistic and immature at time of writing. No doubt I'll come up with something better as time goes on. It alerts via SMS if bad things happen.

## BME280

There's a BME280 sensor attached via i2c, used to monitor temperature, pressure, and humidity.

## MegaIO hat

Most other things attached to the load output of the SmartSolar controller can be controlled via the relays on the MegaIO hat. Currently the fence, the IP cameras, and hypothetical lighting (not yet deployed) can be controlled via the index page. There is the ability to specify an auto timeout on the relays if they are particularly power hungry and apt to be accidentally left on, such as the cameras.

## E3372 LTE dongle

The Pi has a E3372 Huawei dongle that it uses to connect 3 UK LTE. From there it establishes a connection to darksky.io which proxies requests to and from the Pi. Occassionally the dongle will disconnect from the internet for no reason, so there is a connection checking function, as well as functions to control the connection state and even reboot the dongle if required. There is another function that retrieves current information from the dongle regarding network type, data transmitted and connection state. It is possible to send SMS messages from the dongle, but it is cheaper to use an SMS gateway.

## SMS gateway

By default if the internet is available, SMS messages are sent via the clickatell REST API. If the internet is not available the LTE dongle is used instead.

## Environment agency

There is a river level monitoring station on the river in the field, data from this is acquired using the API from the environment agency. Alerts are sent if the river exceeds a specified level, and keeps warning if the river level continues to climb.

## static/index.html

Literally just a page with buttons. Will ideally reflect current state of relays and show battery/pv/weather/river info. Historical data not required but might be nice over a 24h period.
