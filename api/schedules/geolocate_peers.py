#
# Performs optional geolocation of peer connections by IP address for mapping
# Only if Maxmind license file is found at /root/.chia/machinaris/config/maxmind_license.json 
#

import ast
import datetime
import geoip2.webservice
import json
import os
import re
import traceback

from common.models import connections as co
from common.config import globals
from api import app

MAXMIND_LICENSE_FILE = '/root/.chia/machinaris/config/maxmind_license.json'
GEOIP_CACHE_FILE = '/root/.chia/machinaris/cache/geoip_cache.json'

MISSING_LOCATION_RETRY_HOURS = 24
last_missing_location_retry_time = None

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

def save_geoip_cache(data):
    try:
        with open(GEOIP_CACHE_FILE, 'w') as f:
            json.dump(data, f)
    except Exception as ex:
        app.logger.error("Failed to store geoip cache in {0} because {1}".format(GEOIP_CACHE_FILE, str(ex)))

def geolocate_ip_addresses(ip_addresses):
    global last_missing_location_retry_time
    license = load_maxmind_license()
    if not license:
        app.logger.info("Skipping geolocation of peer connections by IP address as no Maxmind license found.")
        return
    geoip_cache = load_geoip_cache()
    missing_retry = False
    if not last_missing_location_retry_time or last_missing_location_retry_time <= \
        (datetime.datetime.now() - datetime.timedelta(hours=MISSING_LOCATION_RETRY_HOURS)):
        missing_retry = True  # Since its been a while, retry all missing locations for ips
        last_missing_location_retry_time = datetime.datetime.now()
    with geoip2.webservice.Client(license["account"], license['license_key'], host="geolite.info") as client:
        for ip_address in ip_addresses:
            if ip_address in geoip_cache:
                if geoip_cache[ip_address]:
                    continue
                if not missing_retry:
                    continue  # Don't request location too often for IPs which weren't resolved earlier
                else:
                    app.logger.info("Retrying {0}, as previously returned {1}.".format(ip_address, geoip_cache[ip_address]))
            try:
                response = client.city(ip_address)
                app.logger.info("{0} located at {1}".format(ip_address, response.location))
                geoip_cache[ip_address] = { 
                    'latitude': response.location.latitude, 
                    'longitude': response.location.longitude, 
                }
                try:
                    geoip_cache[ip_address]['city'] = ast.literal_eval(str(response.city.names))
                except:
                    pass
                try:
                    geoip_cache[ip_address]['country'] = ast.literal_eval(str(response.country.names))
                except:
                    pass
            except Exception as ex:
                geoip_cache[ip_address] = None
                app.logger.info("Failed to query Maxmind city web service for {0} because {1}.".format(ip_address, str(ex)))
    save_geoip_cache(geoip_cache)

def execute():
    with app.app_context():
        from api import db
        gc = globals.load()
        if not gc['is_controller']:
            return # Only controller should attempt geolocation
        ip_addresses = []
        for connection in db.session.query(co.Connection).all():
            for line in connection.details.split('\n'):
                match = re.search(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', line.strip())
                if match and match.group() != "127.0.0.1":
                    #app.logger.info("Adding {0}".format(match.group()))
                    ip_addresses.append(match.group())
        geolocate_ip_addresses(ip_addresses)
