from darksky.api import DarkSky, DarkSkyAsync
from darksky.types import languages, units, weather
from yaml_config import config
import global_vars
import logging
import colorlog

handler = colorlog.StreamHandler()
handler.setFormatter(global_vars.log_format)
logger = colorlog.getLogger(__name__)
logger.addHandler(handler)
logger.setLevel(global_vars.log_level)

weather_data = {}
weather_data['site'] = {}
weather_data['current'] = {}
weather_data['hour'] = {}
weather_data['day'] = {}
weather_data['alert'] = {}

# There's a lot of data we aren't interested in
interesting_items = [
'time',
'summary',
'icon',
'precip_intensity',
'precip_intensity_max',
'precip_probability',
'precip_type',
'precipAccumulation',
'temperature',
'temperature_high',
'temperature_low',
'apparent_temperature',
'apparent_temperature_high',
'apparent_temperature_low',
'dew_point',
'humidity',
'pressure',
'wind_speed',
'wind_gust',
'wind_bearing',
'cloud_cover',
'uv_index',
'visibility'
'ozone',
'nearest_storm_distance',
'nearest_storm_bearing',
]

# Items we're interested in but they need converting to a real (0-100) percentage
percentage_items = [
'precip_probability',
'cloud_cover',
'humidity'
]

alert_items = [
'title',
'severity',
'description',
]

def get_weather_forecast():
    try:
        if not len(weather_data['site']):
            weather_data['site']['latitude'] = config['field']['latitude']
            weather_data['site']['longitude'] = config['field']['longitude']
            weather_data['site']['timezone'] = config['field']['timezone']

        darksky = DarkSky(config['weather']['api_key'])
        forecast = darksky.get_forecast(
            config['field']['latitude'],
            config['field']['longitude'],
            lang=config['weather']['language'],
            units=config['weather']['units'],
            exclude=[weather.MINUTELY, weather.FLAGS],
            timezone=config['field']['timezone'],
        )

        # We're not interested in ALL the data
        all_weather = {
        # Only current weather
        'current': forecast.currently.__dict__,
        # Weather in the next hour
        'hour': forecast.hourly.data[1].__dict__,
        # And the weather for the day
        'day': forecast.daily.data[0].__dict__,
        }

        # And the weather for the day
        for time_period in all_weather:
            for forecast_item in all_weather[time_period]:
                if forecast_item in interesting_items:
                    if forecast_item == 'time':
                        time_iso = all_weather[time_period][forecast_item].replace(tzinfo=None).isoformat()
                        weather_data[time_period][forecast_item] = time_iso
                    elif forecast_item in percentage_items:
                        weather_data[time_period][forecast_item] = int(all_weather[time_period][forecast_item] * 100)
                    else:
                        weather_data[time_period][forecast_item] = all_weather[time_period][forecast_item]

        if forecast.alerts:
            for item in alert_items:
                weather_data['alert'][item] = forecast.alerts[0].__dict__[item]
            if 'red' in weather_data['alert']['title'].lower():
                weather_data['alert']['colour'] = 'red'
            elif 'yellow' in weather_data['alert']['title'].lower():
                weather_data['alert']['colour'] = 'yellow'
            else:
                weather_data['alert']['colour'] = 'info'
        else:
            weather_data['alert']['title'] = None
            weather_data['alert']['colour'] = None
            weather_data['alert']['severity'] = None
            weather_data['alert']['description'] = None

    except Exception as e:
        logger.error('Unhandled exception in retrieving weather forecast: ' + str(e))
