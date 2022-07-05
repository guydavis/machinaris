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
    app.logger.info("Executing status_points...")
    with app.app_context():
        try:
            for blockchain in globals.enabled_blockchains():
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
        except Exception as ex:
            app.logger.info("Failed to load and send signage points because {0}".format(str(ex)))