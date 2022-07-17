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
    app.logger.info("Executing status_drives...")
    with app.app_context():
        try:
            hostname = utils.get_hostname()
            payload = []
            for blockchain in globals.enabled_blockchains():
                for drive in smartctl.load_drives_status():
                    payload.append({
                        "serial_number": drive.serial_number,
                        "hostname": hostname,
                        "blockchain": blockchain,
                        "model_family": drive.model_family,
                        "device_model": drive.device_model,
                        "device": drive.device,
                        "type": drive.type,
                        "comment": drive.comment,
                        "status": drive.status,
                        "temperature": drive.temperature,
                        "power_on_hours": drive.power_on_hours,
                        "size_gibs": drive.size_gibs,
                        "capacity": drive.capacity,
                        "smart_info": drive.smart_info,
                    })
            utils.send_post('/drives/', payload, debug=False)
        except Exception as ex:
            app.logger.info("Failed to load and send drives status because {0}".format(str(ex)))
            traceback.print_exc()
