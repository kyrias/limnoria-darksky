import json
from functools import lru_cache
from urllib.parse import urlunsplit, urlencode

from supybot import utils
from geopy.geocoders import GoogleV3


def retrying_get_url_content(url, retries=0):
    try:
        return utils.web.getUrlContent(url, timeout=10)
    except utils.web.Error as e:
        if retries <= 1:
            raise
        return retrying_get_url_content(url, retries=retries-1)


@lru_cache(maxsize=128)
def get_coordinates(api_key, location):
    geonames = GoogleV3(api_key=api_key, timeout=2)
    return geonames.geocode(location)

def get_forecast(api_key, location, retries=0):
    query = {
        'lat': str(location.latitude),
        'lon': str(location.longitude),
        'units': 'metric',
        'exclude': ','.join(['minutely', 'hourly', 'daily', 'alerts']),
        'appid': api_key,
    }

    url = urlunsplit((
        'https',
        'api.openweathermap.org',
        'data/3.0/onecall',
        urlencode(query),
        None,
    ))

    response = retrying_get_url_content(url, retries=retries)
    return json.loads(response)

directions = [
    'N', 'NNE', 'NE', 'ENE',
    'E', 'ESE', 'SE', 'SSE',
    'S', 'SSW', 'SW', 'WSW',
    'W', 'WNW', 'NW', 'NNW',
]
def bearing_to_cardinal(bearing):
    # Offset bearing by a 16th for accuracy
    offset_bearing = (bearing + 11.25) % 360
    return directions[int(offset_bearing // 22.5) % 16]


def format_forecast(forecast, location):
    currently = forecast['currently']
    output = []

    output.append('Current weather for {}'.format(location.address))

    if currently['weather']:
        output.append(currently['weather'][0]['description'])

    if 'temp' in currently:
        text = 'Temperature {temp:.0f} °C'.format(
            temp=currently['temp'],
        )
        if 'feels_like' in currently \
                and currently['feels_like'] != currently['temperature']:
            text += ' (Feels like {apparent_temp:.0f} °C)'.format(
                apparent_temp=currently['feels_like'],
            )
        output.append(text)

    if 'rain' in currently:
        output.append(
            'Rain {} mm/h'.format(currently['rain']['1h']),
        )

    if 'snow' in currently:
        output.append(
            'Snow {} mm/h'.format(currently['snow']['1h']),
        )

    if 'humidity' in currently:
        output.append('Humidity {:.0f}%'.format(currently['humidity']))

    if 'dew_point' in currently:
        output.append('Dew point {:.0f}°C'.format(currently['dew_point']))

    if 'uvi' in currently:
        output.append('UV index {}'.format(currently['uvi']))

    if 'pressure' in currently:
        output.append('Pressure {:.0f} hPa'.format(currently['pressure']))

    if 'wind_speed' in currently:
        section = 'Wind speed {} m/s'.format(currently['wind_speed'])

        if 'wind_deg' in currently:
            section += ' {cardinal} ({bearing}°)'.format(
                cardinal=bearing_to_cardinal(currently['wind_deg']),
                bearing=currently['wind_deg'],
            )

        output.append(section)

    if 'wind_gust' in currently:
        output.append('Wind gusts {} m/s'.format(currently['wind_gust']))

    if 'clouds' in currently:
        output.append('Cloud cover {:.0f}%'.format(currently['clouds']))

    if 'visibility' in currently:
        visibility = currently['visibility']
        if visibility >= 10:
            output.append('Visibility 10+ km')
        else:
            output.append('Visibility {:.1f} km'.format(visibility))

    return ' :: '.join(output)
