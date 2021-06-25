#
# Performs a REST call to controller (possibly localhost) of latest public wallet status.
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
        #app.logger.info("Skipping public wallet status collection on non-farming instance.")
        return
    with app.app_context():
        try:
            hostname = utils.get_hostname()
            public_wallet = chia_cli.load_wallet_show()
            payload = {
                "hostname": hostname,
                "details": public_wallet.text.replace('\r', ''),
            }
            #app.logger.info(payload)
            utils.send_post('/wallets/', payload, debug=False)
        except:
            app.logger.info("Failed to load and send public wallet status.")
            app.logger.info(traceback.format_exc())
