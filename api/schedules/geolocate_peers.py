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

from common.models import connections as co, workers as wk
from common.config import globals
from api import app, utils

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
                #app.logger.info("GEOLOCATE: Have a cache entry for {0}".format(ip_address))
                if geoip_cache[ip_address]:
                    #app.logger.info("GEOLOCATE: Already have a valid location for {0} at {1}".format(ip_address, geoip_cache[ip_address]))
                    continue
                elif not missing_retry:
                    app.logger.info("GEOLOCATE: No valid location, but not retrying yet. {0}".format(ip_address))
                    continue  # Don't request location too often for IPs which weren't resolved earlier
                else:
                    app.logger.info("GEOLOCATE: Retrying {0}, as previously returned {1}.".format(ip_address, geoip_cache[ip_address]))
            try:
                app.logger.info("GEOLOCATE: Querying maxmind for a valid location of {0}".format(ip_address))
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

def disconnect_denied_connections(connections, geoip_cache, deny_countries):
    if isinstance(deny_countries, str):
        deny_countries = deny_countries.split(',')
    denied_countries = {str(country).strip().casefold() for country in deny_countries if str(country).strip()}
    if not denied_countries:
        return

    denied_node_ids = {}
    for connection in connections:
        for line in connection.details.split('\n'):
            values = line.strip().split()
            if len(values) <= 7:
                continue
            ip_address = values[1]
            node_id = values[3].replace('...', '')
            geoip = geoip_cache.get(ip_address)
            country = geoip.get('country', {}).get('en', '') if geoip else ''
            if node_id and country.casefold() in denied_countries:
                key = (connection.hostname, connection.blockchain, country)
                denied_node_ids.setdefault(key, []).append(node_id)

    if denied_node_ids:
        for (hostname, blockchain, country), node_ids in denied_node_ids.items():
            app.logger.info("Disconnecting %s peer connection(s) from denied country %s for %s on %s.",
                len(node_ids), country, hostname, blockchain)
            remove_connection(node_ids, hostname, blockchain, country)

def remove_connection(node_ids, hostname, blockchain, country):
    from api import db

    try:
        worker = db.session.query(wk.Worker).filter(
            wk.Worker.hostname == hostname,
            wk.Worker.blockchain == blockchain
        ).first()
        if not worker:
            app.logger.error("Unable to remove connections: worker %s for %s was not found.", hostname, blockchain)
            return False
        response = utils.send_worker_post(worker, "/actions/", {
            'service': 'networking',
            'action': 'remove_connection',
            'blockchain': blockchain,
            'node_ids': node_ids
        })
        response.raise_for_status()
    except Exception as ex:
        app.logger.error("Failed to remove connections from %s for %s on %s: %s",
            country, hostname, blockchain, str(ex))
        return False
    app.logger.info("Successfully requested removal of %s connection(s) from denied country %s for %s on %s.",
        len(node_ids), country, hostname, blockchain)
    return True

def execute():
    with app.app_context():
        from api import db
        gc = globals.load()
        if not gc['is_controller']:
            return # Only controller should attempt geolocation
        ip_addresses = []
        connections = db.session.query(co.Connection).all()
        for connection in connections:
            for line in connection.details.split('\n'):
                match = re.search(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', line.strip())
                if match and match.group() != "127.0.0.1":
                    #app.logger.info("Adding {0}".format(match.group()))
                    ip_addresses.append(match.group())
        geolocate_ip_addresses(ip_addresses)
        disconnect_denied_connections(connections, load_geoip_cache(),
            app.config.get('CONNECTION_DENY_COUNTRIES', []))
