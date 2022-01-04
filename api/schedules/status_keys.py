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
from api.commands import chia_cli, mmx_cli
from api import app
from api import utils

def update():
    with app.app_context():
        try:
            hostname = utils.get_hostname()
            for blockchain in globals.enabled_blockchains():
                if blockchain == 'mmx':
                    public_keys = mmx_cli.load_keys_show(blockchain)
                else:
                    public_keys = chia_cli.load_keys_show(blockchain)
                payload = {
                    "hostname": hostname,
                    "blockchain": blockchain,
                    "details": public_keys.text.replace('\r', ''),
                }
                utils.send_post('/keys/', payload, debug=False)
        except:
            app.logger.info("Failed to load and send public keys status.")
            app.logger.info(traceback.format_exc())
