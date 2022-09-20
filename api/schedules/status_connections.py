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
from api.commands import chia_cli, mmx_cli
from api import app
from api import utils

def update():
    with app.app_context():
        try:
            for blockchain in globals.enabled_blockchains():
                hostname = utils.get_hostname()
                if blockchain == 'mmx':
                    connections = mmx_cli.load_connections_show(blockchain)
                else:
                    connections = chia_cli.load_connections_show(blockchain)
                payload = {
                    "hostname": hostname,
                    "blockchain": blockchain,
                    "details": connections.text.replace('\r', ''),
                }
                utils.send_post('/connections/', payload, debug=False)
        except Exception as ex:
            app.logger.info("Failed to load and send connection status because {0}".format(str(ex)))

