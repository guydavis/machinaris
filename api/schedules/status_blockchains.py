#
# Performs a REST call to controller (possibly localhost) of latest blockchain status.
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
        #app.logger.info("Skipping blockchains status collection on non-farming instance.")
        return
    with app.app_context():
        try:
            hostname = utils.get_hostname()
            blockchain = chia_cli.load_blockchain_show()
            #app.logger.info(blockchain.text)
            payload = {
                "hostname": hostname,
                "details": blockchain.text.replace('\r', ''),
            }
            utils.send_post('/blockchains/', payload, debug=False)
        except:
            app.logger.info("Failed to load and send blockchains status.")
            app.logger.info(traceback.format_exc())
