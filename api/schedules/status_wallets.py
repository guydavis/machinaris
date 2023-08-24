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
from api.commands import chia_cli, mmx_cli
from api import app
from api import utils

def update():
    with app.app_context():
        try:
            blockchain = globals.enabled_blockchains()[0]
            hostname = utils.get_hostname()
            if blockchain == 'mmx':
                public_wallet = mmx_cli.load_wallet_show(blockchain)
            else:
                public_wallet = chia_cli.load_wallet_show(blockchain)
            if public_wallet:
                payload = {
                    "hostname": hostname,
                    "blockchain": blockchain,
                    "details": public_wallet.text.replace('\r', ''),
                }
                #app.logger.info(payload)
                utils.send_post('/wallets/', payload, debug=False)
            else:
                app.logger.info("Not sending public wallet status as wallet is not running.")
        except Exception as ex:
            app.logger.info("Failed to load and send public wallet status because {0}".format(str(ex)))
