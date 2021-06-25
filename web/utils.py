#
# Util methods for web
#

import http
import json
import os
import requests
import socket

from web import app

def send_get(worker, path, query_params={}, timeout=30, debug=False):
    if debug:
        http.client.HTTPConnection.debuglevel = 1
    response = requests.get(worker.url + path, params = query_params, timeout=timeout)
    http.client.HTTPConnection.debuglevel = 0
    return response

def send_post(worker, path, payload, debug=False):
    headers = {'Content-type': 'application/json', 'Accept': 'application/json'}
    if debug:
        http.client.HTTPConnection.debuglevel = 1
    response = requests.post(worker.url + path, headers = headers, data = json.dumps(payload))
    http.client.HTTPConnection.debuglevel = 0
    return response

def send_put(worker, path, payload, debug=False):
    headers = {'Content-type': 'application/json', 'Accept': 'application/json'}
    if debug:
        http.client.HTTPConnection.debuglevel = 1
    response = requests.put(worker.url + path, headers = headers, data = json.dumps(payload))
    http.client.HTTPConnection.debuglevel = 0
    return response

def send_delete(worker, path, debug=False):
    headers = {'Content-type': 'application/json', 'Accept': 'application/json'}
    if debug:
        http.client.HTTPConnection.debuglevel = 1
    response = requests.delete(worker.url + path, headers = headers)
    http.client.HTTPConnection.debuglevel = 0
    return response

def get_controller_url():
    return "{0}://{1}:{2}".format(
        app.config['CONTROLLER_SCHEME'],
        app.config['CONTROLLER_HOST'],
        app.config['CONTROLLER_PORT']
    )

def get_controller_web():
    return "http://{0}:8926".format(
        app.config['CONTROLLER_HOST']
    )

def get_hostname():
    if 'worker_address' in os.environ:
        hostname = os.environ['worker_address']
    else:
        hostname = socket.gethostname()
    return hostname

def is_controller():
    return app.config['CONTROLLER_HOST'] == "localhost"
