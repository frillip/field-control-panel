# Field Control Panel

Based on a Raspberry Pi 4 B, with a MegaIO hat. Goal is to have a web based interface that automatically populates with useful information and the state of the various systems. Also used to control various things on the field, eg, the electric fencing to the ~~velociraptor~~ horse/sheep paddocks, power supply to the IP cameras overseeing the ~~embryo storage fecility~~ field shelter, and exterior lighting around the ~~east dock~~ entrance gateway.

Currently the control panel page is a ~~static set of buttons~~ a fancy auto-updating readout of everything that is happening at the field, most useful data can be obtained programmatically via JSON if required.

## Scheduler

Most tasks are run off a scheduler, exceptions being the VE.Direct interface tasks as these are synchronous serial tasks, and the aiohttp web server.

## Web server

The main index page and JSON outputs are presented using the aiohttp web server on http://localhost:8080/ . This is proxied by apache running on the Pi which takes care of access control and HTTPS.

## Configuration

This is done in `config.yaml`. An example is provided. Some parameters are required, others are optional If missing from the yaml, the optional parameters will be populated with a default. Errors are thrown for missing required parameters, and the application will exit. Warnings are flagged for unrecognised options.

## VE.Direct interface

Currently there are functions to read information from Victron modules (currently a SmartSolar 100|20 and BMV-712) over VE.Direct USB interfaces. Currently this is via the human-readable VE.Direct protocol which is automatically output every second or so by the module. Ideally in the future this should be requested and read back using the Victron HEX protocol (see issue #48), or, even better, via Bluetooth (see issue #14), however the Bluetooth protocol is not opensourced like the HEX protocol. This would also allow control of the modules.

There are also functions to check the overall health of the system, but these are relatively simplistic and immature at time of writing. No doubt I'll come up with something better as time goes on. It alerts via SMS if bad things happen.

## Sensors

There's a BME280 sensor attached via i2c, used to monitor temperature, pressure, and humidity. There is also a TSL2561 ambient light sensor present, and a GPS module, currently used for timekeeping, but maybe in the future for automatic detection of location for weather etc.

## MegaIO hat

Most other things attached to the load output of the SmartSolar controller can be controlled via the relays on the MegaIO hat. Currently the fence, the IP cameras, and hypothetical lighting (not yet deployed) can be controlled via the index page. There is the ability to specify an auto timeout on the relays if they are particularly power hungry and apt to be accidentally left on, such as the cameras.

## E3372 LTE dongle

The Pi has a E3372 Huawei dongle that it uses to connect 3 UK LTE. From there it establishes a connection to darksky.io which proxies requests to and from the Pi. Occassionally the dongle will disconnect from the internet for no reason, so there is a connection checking function, as well as functions to control the connection state and even reboot the dongle if required. There is another function that retrieves current information from the dongle regarding network type, data transmitted and connection state. It is possible to send SMS messages from the dongle, but it is cheaper to use an SMS gateway.

## SMS gateway

By default if the internet is available, SMS messages are sent via the clickatell REST API. If the internet is not available the LTE dongle is used instead.

## Environment agency

There is a river level monitoring station on the river in the field, data from this is acquired using the API from the environment agency. Alerts are sent if the river exceeds a specified level, and keeps warning if the river level continues to climb.

## Weather <a href="https://darksky.net/poweredby/"><img src="https://darksky.net/dev/img/attribution/poweredby-oneline.png" align="center" width=150></img></a>

Weather data used to be obtained from the met office, but their API proved to be unreliable with poor library support. Data is now obtained from darksky.net. This is based off the co-ordinates specified in the YAML, however they may be automatically obtained via GPS instead in the future.

## static/index.html

Now has fancy toggle switches that reflect the current state of relays. Also shows PV/Battery/Environment data. Updates by pulling JSON every 1s for relays, 5s for PV/Battery, and only on load for temperature/weather.

## static/style.css

Where the terrible CSS lives!

