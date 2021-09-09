#
# Performs a REST call to controller (possibly localhost) of latest plotnft status.
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
            blockchains = ['chia']
            # Flax doesn't support this yet.
            #if globals.flax_enabled():  
            #    blockchains.append('flax')
            for blockchain in blockchains:
                hostname = utils.get_hostname()
                plotnft = chia_cli.load_plotnft_show(blockchain)
                payload = {
                    "hostname": hostname,
                    "blockchain": blockchain,
                    "details": plotnft.text.replace('\r', ''),
                }
                #app.logger.info(payload)
                utils.send_post('/plotnfts/', payload, debug=False)
        except:
            app.logger.info("Failed to load and send plotnft status.")
            app.logger.info(traceback.format_exc())
