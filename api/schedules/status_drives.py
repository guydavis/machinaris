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
from api.commands import smartctl
from api import app
from api import utils

def update():
    with app.app_context():
        try:
            hostname = utils.get_hostname()
            payload = []
            for blockchain in globals.enabled_blockchains():
                for drive in smartctl.load_drive_status():
                    payload.append({
                        "hostname": hostname,
                        "blockchain": blockchain,
                        "details": drive,
                    })
            utils.send_post('/drives/', payload, debug=True)
        except:
            app.logger.info("Failed to load and send drive status.")
            app.logger.info(traceback.format_exc())
