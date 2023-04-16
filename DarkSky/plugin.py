###
# Copyright (c) 2019, Johannes Löthberg
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#   * Redistributions of source code must retain the above copyright notice,
#     this list of conditions, and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions, and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#   * Neither the name of the author of this software nor the name of
#     contributors to this software may be used to endorse or promote products
#     derived from this software without specific prior written consent.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

###

import json

from supybot import utils, plugins, ircutils, callbacks
from supybot.commands import *
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('DarkSky')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x
from geopy.exc import GeocoderTimedOut

from .local import utils as local_utils


class DarkSky(callbacks.Plugin):
    """Weather lookups using the OpenWeather and GeoNames"""
    threaded = True

    def forecast(self, irc, msg, args, location):
        """<location>

        Looks up the given location using GeoNames and gets the forecast for
        the retrieved coordinates from OpenWeather.
        """
        try:
            loc = local_utils.get_coordinates(
                self.registryValue('googleMapsApiKey'),
                location,
            )
        except GeocoderTimedOut:
            irg.error('Location lookup timed out')
            return

        if not loc:
            irc.error(
                'Could not look up location {!r}, does that place even exist?'
                .format(location)
            )
            return

        try:
            forecast = local_utils.get_forecast(
                self.registryValue('darkSkyApiKey'),
                loc,
            )
        except utils.web.Error as e:
            self.log.error('Could not look up forecast: {!r}'.format(str(e)))
            irc.error('Could not look up forecast: {!r}'.format(str(e)))
            return

        self.log.debug('Forecast response: {}'.format(json.dumps(forecast)))
        formatted = local_utils.format_forecast(forecast, loc)
        irc.reply(formatted)
    forecast = wrap(forecast, ['text'])


Class = DarkSky


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
