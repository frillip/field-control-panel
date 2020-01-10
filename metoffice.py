import requests
from time import sleep
from datetime import datetime,timedelta,timezone
import global_vars
from yaml_config import config
import logging
import colorlog
from pprint import pprint

handler = colorlog.StreamHandler()
handler.setFormatter(global_vars.log_format)
logger = colorlog.getLogger(__name__)
logger.addHandler(handler)
logger.setLevel(global_vars.log_level)

weather_type = {
    'NA': 'Not available',
    '0': 'Clear night',
    '1': 'Sunny day',
    '2': 'Partly cloudy',
    '3': 'Partly cloudy',
    '4': 'Not used',
    '5': 'Mist',
    '6': 'Fog',
    '7': 'Cloudy',
    '8': 'Overcast',
    '9': 'Light rain shower',
    '10': 'Light rain shower',
    '11': 'Drizzle',
    '12': 'Light rain',
    '13': 'Heavy rain shower',
    '14': 'Heavy rain shower',
    '15': 'Heavy rain',
    '16': 'Sleet shower',
    '17': 'Sleet shower',
    '18': 'Sleet',
    '19': 'Hail shower',
    '20': 'Hail shower',
    '21': 'Hail',
    '22': 'Light snow shower',
    '23': 'Light snow shower',
    '24': 'Light snow',
    '25': 'Heavy snow shower',
    '26': 'Heavy snow shower',
    '27': 'Heavy snow',
    '28': 'Thunder shower',
    '29': 'Thunder shower',
    '30': 'Thunder'
}

uv_index = {
    0: 'None',
    1: 'Low',
    2: 'Low',
    3: 'Moderate',
    4: 'Moderate',
    5: 'Moderate',
    6: 'High',
    7: 'High',
    8: 'Very high',
    9: 'Very high',
    10: 'Very high',
    11: 'Extreme'
}

visibility = {
    'UN': 'Unknown',
    'VP': 'Very poor',
    'PO': 'Poor',
    'MO': 'Moderate',
    'GO': 'Good',
    'VG': 'Very good',
    'EX': 'Excellent'
}

def get_weather_forecast():
    params = {}
    params['key'] = config['metoffice']['api_key']
    params['res'] = '3hourly'
    try:
        resp = requests.get(config['metoffice']['api_url'],
                            params=params)
        forecast_data = resp.json()
        if not forecast_data['SiteRep']['DV'].get('Location'):
            logger.error('Failed to get weather forecast, will retry in 300s')
            return

        next_forecast = forecast_data['SiteRep']['DV']['Location']['Period'][0]['Rep'][0]
        forecast_date_string = forecast_data['SiteRep']['DV']['Location']['Period'][0]['value']
        forecast_date = datetime.strptime(forecast_date_string, '%Y-%m-%dZ')
        forecast_data['SiteRep']['DV']['Location'].pop('Period', None)

        global_vars.weather_data['site']=forecast_data['SiteRep']['DV']['Location']

        for field in next_forecast:
            if field == 'D':
                global_vars.weather_data['wind_direction'] = next_forecast['D']

            elif field == 'F':
                global_vars.weather_data['feels_like'] = int(next_forecast['F'])

            elif field == 'G':
                global_vars.weather_data['wind_gust'] = int(next_forecast['G'])

            elif field == 'H':
                global_vars.weather_data['humidity'] = int(next_forecast['H'])

            elif field == 'P':
                global_vars.weather_data['pressure'] = int(next_forecast['P'])

            elif field == 'Pp':
                global_vars.weather_data['precipitation_chance'] = int(next_forecast['Pp'])

            elif field == 'S':
                global_vars.weather_data['wind_speed'] = int(next_forecast['S'])

            elif field == 'T':
                global_vars.weather_data['temperature'] = int(next_forecast['T'])

            elif field == 'U':
                global_vars.weather_data['uv_index'] = int(next_forecast['U'])

                if global_vars.weather_data['uv_index'] > 11:
                    global_vars.weather_data['uv_index'] = 11
                    global_vars.weather_data['uv_index_text'] = 'Extreme'

                elif global_vars.weather_data['uv_index'] < 0:
                    global_vars.weather_data['uv_index'] = 0
                    global_vars.weather_data['uv_index_text'] = 'None'

                else:
                    global_vars.weather_data['uv_index_text'] = uv_index[global_vars.weather_data['uv_index']]

            elif field == 'V':

                if next_forecast['V'] in visibility:
                    global_vars.weather_data['visibility'] = next_forecast['V']
                    global_vars.weather_data['visibility_text'] = visibility[next_forecast['V']]

                else:
                    global_vars.weather_data['visibility'] = 'UN'
                    global_vars.weather_data['visibility_text'] = 'Unknown'

            elif field == 'W':
                global_vars.weather_data['weather_type'] = next_forecast['W']

                if global_vars.weather_data['weather_type'] in weather_type:
                    global_vars.weather_data['weather_type_text'] = weather_type[global_vars.weather_data['weather_type']]

                else:
                    global_vars.weather_data['weather_type'] = 'NA'
                    global_vars.weather_data['weather_type_text'] = 'Not available'

            elif field == '$':
                forecast_period = (forecast_date+timedelta(seconds=(1260*60))).replace(tzinfo=None)
                global_vars.weather_data['forecast_period'] = forecast_period.isoformat()

        pass

    except Exception as e:
        logger.error('Met office forecast task failed: ' + str(e))
        pass
