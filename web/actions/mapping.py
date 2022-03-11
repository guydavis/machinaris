#
# Performs optional geolocation of peer connections by IP address for mapping
# Only if Maxmind license file is found at /root/.chia/machinaris/config/maxmind_license.json 
#

import ast
from marshmallow import validates_schema

from pytest import mark
import geoip2.webservice
import json
import os
import re
import traceback

from common.models import connections as co
from common.config import globals
from api import app

MAXMIND_LICENSE_FILE = '/root/.chia/machinaris/config/maxmind_license.json'
MAPBOX_LICENSE_FILE = '/root/.chia/machinaris/config/mapbox_license.json'
GEOIP_CACHE_FILE = '/root/.chia/machinaris/cache/geoip_cache.json'

def load_maxmind_license():
    if not os.path.exists(MAXMIND_LICENSE_FILE):
        return None
    try:
        with open(MAXMIND_LICENSE_FILE) as f:
            data = json.load(f)
    except Exception as ex:
        msg = "Unable to valid json from {0} because {1}".format(MAXMIND_LICENSE_FILE, str(ex))
        app.logger.error(msg)
    return data

def load_mapbox_license():
    if not os.path.exists(MAPBOX_LICENSE_FILE):
        return None
    try:
        with open(MAPBOX_LICENSE_FILE) as f:
            data = json.load(f)
    except Exception as ex:
        msg = "Unable to valid json from {0} because {1}".format(MAPBOX_LICENSE_FILE, str(ex))
        app.logger.error(msg)
    return data

def save_settings(maxmind_account, maxmind_license_key, mapbox_access_token):
    try:
        with open(MAXMIND_LICENSE_FILE, 'w') as f:
            json.dump({"account": maxmind_account.strip(), "license_key": maxmind_license_key.strip()}, f)
    except Exception as ex:
        app.logger.error("Failed to store Maxmind settings in {0} because {1}".format(MAXMIND_LICENSE_FILE, str(ex)))
    if mapbox_access_token and mapbox_access_token.strip():
        try:
            with open(MAPBOX_LICENSE_FILE, 'w') as f:
                json.dump({"access_token": mapbox_access_token.strip()}, f)
        except Exception as ex:
            app.logger.error("Failed to store Mapbox settings in {0} because {1}".format(MAPBOX_LICENSE_FILE, str(ex)))

def load_geoip_cache():
    data = {}
    if os.path.exists(GEOIP_CACHE_FILE):
        try:
            with open(GEOIP_CACHE_FILE) as f:
                data = json.load(f)
        except Exception as ex:
            msg = "Unable to read geoip cache from {0} because {1}".format(GEOIP_CACHE_FILE, str(ex))
            app.logger.error(msg)
            return data
    return data

def generate_marker_hues(connections):
    marker_hues = {}
    count = len(connections.rows)
    index = 0
    for connection in connections.rows:
        marker_hues[connection['blockchain']] = 360/count * index
        index += 1
    #app.logger.info(marker_hues)
    return marker_hues