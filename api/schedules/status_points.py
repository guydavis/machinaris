#
# Performs a REST call to controller (possibly localhost) of latest points status.
#

import asyncio
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
from api.rpc import chia
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
                points =  asyncio.run(chia.get_signage_points(blockchain))
                payload = {
                    "hostname": hostname,
                    "blockchain": blockchain,
                    "details": points,
                }
                for point in points:
                    app.logger.info(point)
                #utils.send_post('/plotnfts/', payload, debug=False)
        except:
            app.logger.info("Failed to load and send recent signage points.")
            app.logger.info(traceback.format_exc())
