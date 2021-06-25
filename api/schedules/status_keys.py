#
# Performs a REST call to controller (possibly localhost) of latest public keys status.
#


import datetime
import http
import json
import os
import requests
import socket
import sqlite3
import traceback

from flask import g

from common.config import globals
from api.commands import chia_cli
from api import app
from api import utils

def update():
    if not globals.farming_enabled():
        #app.logger.info("Skipping public keys status collection on non-farming instance.")
        return
    with app.app_context():
        try:
            hostname = utils.get_hostname()
            public_keys = chia_cli.load_keys_show()
            #app.logger.info(public_keys.text)
            payload = {
                "hostname": hostname,
                "details": public_keys.text.replace('\r', ''),
            }
            utils.send_post('/keys/', payload, debug=False)
        except:
            app.logger.info("Failed to load and send public keys status.")
            app.logger.info(traceback.format_exc())
