#
# Util methods for web
#

import http
import json
import os
import requests
import socket

from web import app

def get_controller_url():
    return "{0}://{1}:{2}".format(
        app.config['CONTROLLER_SCHEME'],
        app.config['CONTROLLER_HOST'],
        app.config['CONTROLLER_PORT']
    )

def get_hostname():
    if 'hostname' in os.environ:
        hostname = os.environ['hostname']
    else:
        hostname = socket.gethostname()
    return hostname

def is_controller():
    return app.config['CONTROLLER_HOST'] == "localhost"
