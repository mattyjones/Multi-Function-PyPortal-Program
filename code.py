# The MIT License (MIT)
#
# Copyright (c) 2019 Michael McGurrin
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

"""
This is the main program for a multi-function Portal app.
It includes current weather, day, date, time, S&P 500, Indoor Temp,
and Shower Thoughts subreddit.
"""
import sys
import time
import board
from adafruit_pyportal import PyPortal
from adafruit_bitmap_font import bitmap_font
cwd = ("/"+__file__).rsplit('/', 1)[0] # the current working directory (where this file is)
sys.path.append(cwd)
import day_graphics          # pylint: disable=wrong-import-position
import openweather_graphics  # pylint: disable=wrong-import-position
import st_graphics           # pylint: disable=wrong-import-position
import market_graphics

linger = 7 # number of seconds to stay on each app
long_linger = 14 # For apps with more text, like shower thoughts

# Get wifi details and more from a secrets.py file
try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise

# Initiate the pyportal
DATA_LOCATION = []
pyportal = PyPortal(json_path=DATA_LOCATION,
                    status_neopixel=board.NEOPIXEL,
                    default_bg=0x000000)

# Get the fonts for all apps
small_font = cwd+"/fonts/Arial-12.bdf"
medium_font = cwd+"/fonts/Arial-16.bdf"
large_font = cwd+"/fonts/Arial-Bold-24.bdf"
small_font = bitmap_font.load_font(small_font)
medium_font = bitmap_font.load_font(medium_font)
large_font = bitmap_font.load_font(large_font)
glyphs = b'0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ-,.: '
small_font.load_glyphs(glyphs)
medium_font.load_glyphs(glyphs)
large_font.load_glyphs(glyphs)
large_font.load_glyphs(('°',))  # a non-ascii character we need for sure

# Weather info
# Use cityname, country code where countrycode is ISO3166 format.
# E.g. "New York, US" or "London, GB" OR use Location Code
LOCATION = "4791160" #Vienna, VA
# Set up where we'll be fetching data from
# You'll need to get a token from openweather.org, looks like 'b6907d289e10d714a6e88b30761fae22'
WX_DATA_SOURCE = "https://api.openweathermap.org/data/2.5/weather?id="+LOCATION
WX_DATA_SOURCE += "&appid="+secrets['openweather_token']

# S&P 500 ("Market Data") info
MARKET_DATA_SOURCE = "https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=INX"
MARKET_DATA_SOURCE += "&apikey="+secrets['alpha_advantage_key']

# Shower thoughts info
ST_DATA_SOURCE = "https://www.reddit.com/r/Showerthoughts/new.json?sort=new&limit=1"

# Loop through all the applications
localtime_refresh = None
weather_refresh = None
st_refresh = None
market_refresh = None
while True:
    # Day, date, and time
     # only query the online time once per hour (and on first run)
    pyportal.set_background(cwd+"/day_bitmap.bmp")
    try:
        if (not localtime_refresh) or (time.monotonic() - localtime_refresh) > 3600:
            print("Getting time from internet!")
            pyportal.get_local_time()
            localtime_refresh = time.monotonic()
        text_group = day_graphics.day_graphics(medium_font = medium_font, large_font = large_font)
        pyportal.splash.append(text_group)
        # Display for seven seconds, then empty the pyportal.splash group so it can be loaded with new display info
        time.sleep(linger)
    except RuntimeError as e:
        print("Some error occured,  skipping this iteration! -", e)
        continue
    pyportal.splash.pop()

    # While there are some differences, could probably refactor the three segments
    # below into one function call

    # Display weather
    # only query the weather every 10 minutes (and on first run)
    pyportal.set_background(cwd+"/wx_bitmap.bmp")
    time.sleep(2)
    try:
        if (not weather_refresh) or (time.monotonic() - weather_refresh) > 600:
            wx = pyportal.fetch(WX_DATA_SOURCE)
            print("Response is", wx)
            weather_refresh = time.monotonic()
        text_group, background_file = openweather_graphics.wx_graphics(medium_font = medium_font,
            large_font = large_font, small_font = small_font, weather = wx)
        pyportal.set_background(cwd+background_file)
        pyportal.splash.append(text_group)
        # Display for 14 seconds, then empty the pyportal.splash group so it can be loaded with new display info
        time.sleep(long_linger)
    except RuntimeError as e:
        print("Some error occured, skipping this iteration! -", e)
        continue
    pyportal.splash.pop()

    # Display Reddit Shower Thoughts
    # only query shower thoughts every 5 minutes (and on first run)
    pyportal.set_background(cwd+"/st_bitmap.bmp")
    time.sleep(2)
    try:
        if (not st_refresh) or (time.monotonic() - st_refresh) > 300:
            print("Getting shower thought from internet!")
            st = pyportal.fetch(ST_DATA_SOURCE)
            print("Response is", st)
            st_refresh = time.monotonic()
        text_group = st_graphics.st_graphics(medium_font = medium_font, large_font = large_font,
            small_font = small_font, st = st)
        pyportal.splash.append(text_group)
        # Display for 14 seconds, then empty the pyportal.splash group so it can be loaded with new display info
        time.sleep(long_linger)
    except RuntimeError as e:
        print("Some error occured,  skipping this iteration! -", e)
        continue
    pyportal.splash.pop()

    # Display S&P 500
    # only query the S&P every 10 minutes (and on first run)
    pyportal.set_background(cwd+"/market_bitmap.bmp")
    time.sleep(2)
    try:
        if (not market_refresh) or (time.monotonic() - market_refresh) > 300:
            print("Getting S&P 500 from internet!")
            market = pyportal.fetch(MARKET_DATA_SOURCE)
            print("Response is", market)
            market_refresh = time.monotonic()
        text_group, background_file = market_graphics.market_graphics(medium_font = medium_font, large_font = large_font,
            market = market)
        pyportal.set_background(cwd+background_file)
        pyportal.splash.append(text_group)
        # Display for 7 seconds, then empty the pyportal.splash group so it can be loaded with new display info
        time.sleep(linger)
    except RuntimeError as e:
        print("Some error occured,  skipping this iteration! -", e)
        continue
    pyportal.splash.pop()