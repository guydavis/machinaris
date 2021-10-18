#
# Performs a REST call to controller (possibly localhost) of latest connections status.
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
    with app.app_context():
        try:
            for blockchain in globals.enabled_blockchains():
                hostname = utils.get_hostname()
                connections = chia_cli.load_connections_show(blockchain)
                #app.logger.info(connections.text)
                payload = {
                    "hostname": hostname,
                    "blockchain": blockchain,
                    "details": connections.text.replace('\r', ''),
                }
                utils.send_post('/connections/', payload, debug=False)
        except:
            app.logger.info("Failed to load and send connections status.")
            app.logger.info(traceback.format_exc())
