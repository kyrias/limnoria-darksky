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
    current = forecast['current']
    output = []

    output.append('Current weather for {}'.format(location.address))

    if current['weather']:
        output.append(current['weather'][0]['description'].title())

    if 'temp' in current:
        text = 'Temperature {temp:.0f} °C'.format(
            temp=current['temp'],
        )
        if 'feels_like' in current \
                and current['feels_like'] != current['temp']:
            text += ' (Feels like {apparent_temp:.0f} °C)'.format(
                apparent_temp=current['feels_like'],
            )
        output.append(text)

    if 'rain' in current:
        output.append(
            'Rain {} mm/h'.format(current['rain']['1h']),
        )

    if 'snow' in current:
        output.append(
            'Snow {} mm/h'.format(current['snow']['1h']),
        )

    if 'humidity' in current:
        output.append('Humidity {:.0f}%'.format(current['humidity']))

    if 'dew_point' in current:
        output.append('Dew point {:.0f}°C'.format(current['dew_point']))

    if 'uvi' in current:
        output.append('UV index {}'.format(current['uvi']))

    if 'pressure' in current:
        output.append('Pressure {:.0f} hPa'.format(current['pressure']))

    if 'wind_speed' in current:
        section = 'Wind speed {} m/s'.format(current['wind_speed'])

        if 'wind_deg' in current:
            section += ' {cardinal} ({bearing}°)'.format(
                cardinal=bearing_to_cardinal(current['wind_deg']),
                bearing=current['wind_deg'],
            )

        output.append(section)

    if 'wind_gust' in current:
        output.append('Wind gusts {} m/s'.format(current['wind_gust']))

    if 'clouds' in current:
        output.append('Cloud cover {:.0f}%'.format(current['clouds']))

    if 'visibility' in current:
        visibility = current['visibility']
        if visibility >= 10:
            output.append('Visibility 10+ km')
        else:
            output.append('Visibility {:.1f} km'.format(visibility))

    output.append('Provided by OpenWeather')

    return ' :: '.join(output)
