#
# Performs a REST call to controller (possibly localhost) of latest farm status.
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
        app.logger.info(
            "Skipping wallet status collection on non-farming instance.")
        return
    with app.app_context():
        try:
            hostname = utils.get_hostname()
            wallet = chia_cli.load_wallet_show()
            app.logger.info(wallet.text)
            payload = {
                "hostname": hostname,
                "details": wallet.text.replace('\r', ''),
            }
            app.logger.info(payload)
            utils.send_post('/wallets', payload, debug=True)
        except:
            app.logger.info("Failed to load send wallet status.")
            app.logger.info(traceback.format_exc())
