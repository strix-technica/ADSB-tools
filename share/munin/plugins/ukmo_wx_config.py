# encoding: utf-8

# ukmo_wx_config.py Configuration for UK Met Office weather plugin for Munin
# Copyright (c) 2017 David King
# https://github.com/strix-technica/ADSB-tools
#
# NB:
#   - See README for configuration
#   - 'list' mode requires python-geopy installed AND that you've
#     configured your location
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import collections

# --- Configuration begins ---
KEY = '' # see README
LOC = 'all'

# Ordered list of stations to record.  Hint: try executing this script
# similar to "./ukmo_wx list 50" after you've configured the position
PLACES = collections.OrderedDict( [
                (u'3772'  , u'heathrow',),
        ] )

# You can delete any of these you don't want output
GRAPHS = {
             'wx_temp': ('Temperature', u'°C', 'T',),
             'wx_wind_dir': ('Wind direction', u'°', 'D',),
             'wx_wind_spd': ('Wind speed', 'kts', 'S',),
             'wx_press': ('Pressure', 'hPa', 'P',),
             'wx_rh': ('Relative humidity', '%', 'H',),
         }

# Receiver position.  Only required for list output.
RX_LAT    = 51.567
RX_LON    =  0.123
RX_ALT_KM = 108 * 0.0003048 # kilometers per feet
RX_POS    = (RX_LAT, RX_LON, RX_ALT_KM,)
# --- Configuration ends ---
