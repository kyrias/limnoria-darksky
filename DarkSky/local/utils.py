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


def get_forecast(key, location, retries=0):
    path = '/'.join([
        'forecast',
        key,
        ','.join([
            str(location.latitude),
            str(location.longitude)
        ]),
    ])

    query = {
        'units': 'si',
        'exclude': ','.join(['minutely', 'hourly', 'daily', 'alerts']),
    }

    url = urlunsplit((
        'https',
        'api.darksky.net',
        path,
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

    if 'summary' in currently:
        output.append(currently['summary'])

    if 'temperature' in currently:
        text = 'Temperature {temp:.0f} °C'.format(
            temp=currently['temperature'],
        )
        if 'apparentTemperature' in currently \
                and currently['apparentTemperature'] != currently['temperature']:
            text += ' (Feels like {apparent_temp:.0f} °C)'.format(
                apparent_temp=currently['apparentTemperature'],
            )
        output.append(text)

    if 'precipType' in currently \
            and 'precipIntensity' in currently \
            and 'precipProbability' in currently:
        output.append(
            '{type} {intensity} mm/h ({probability:.0f}%)'.format(
                type=currently['precipType'].title(),
                intensity=round(currently['precipIntensity'], 2),
                probability=currently['precipProbability'] * 100,
            ),
        )

    if 'humidity' in currently:
        output.append('Humidity {:.0f}%'.format(currently['humidity'] * 100))

    if 'dewPoint' in currently:
        output.append('Dew point {:.0f}°'.format(currently['dewPoint']))

    if 'uvIndex' in currently:
        output.append('UV index {}'.format(currently['uvIndex']))

    if 'pressure' in currently:
        output.append('Pressure {:.0f} hPa'.format(currently['pressure']))

    if 'windSpeed' in currently:
        fmt = 'Wind speed {speed} m/s'
        if 'windBearing' in currently:
            fmt += ' {cardinal} ({bearing}°)'

        wind_direction = (currently.get('windBearing', 0) + 180) % 360
        output.append(
            fmt.format(
                speed=currently['windSpeed'],
                cardinal=bearing_to_cardinal(wind_direction),
                bearing=wind_direction,
            )
        )

    if 'windGust' in currently:
        output.append('Wind gusts {} m/s'.format(currently['windGust']))

    if 'cloudCover' in currently:
        output.append('Cloud cover {:.0f}%'.format(currently['cloudCover'] * 100))

    if 'visibility' in currently:
        visibility = currently['visibility']
        if visibility >= 16:
            output.append('Visibility 16+ km')
        else:
            output.append('Visibility {:.1f} km'.format(visibility))

    return ' :: '.join(output)
