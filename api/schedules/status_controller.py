#
# Performs a REST call to controller (possibly localhost) of latest farm status.
#


import datetime
import http
import json
import os
import pytz
import requests
import socket
import sqlite3
import traceback

from flask import g

from common.config import globals
from common.models import workers as w
from common.extensions.database import db
from api.commands import chia_cli, chiadog_cli, plotman_cli
from api import app
from api import utils

def update():
    if not utils.is_controller():
        return
    with app.app_context():
        try:
            workers = db.session.query(w.Worker).order_by(w.Worker.hostname).all()
            ping_workers(workers)
            db.session.commit()
        except:
            app.logger.info(traceback.format_exc())
            app.logger.info("Failed to load and send worker status.")

def ping_workers(workers):
    tz = pytz.timezone('Etc/UTC')
    for worker in workers:
        try:
            #app.logger.info("Pinging worker api endpoint: {0}".format(worker.hostname))
            utils.send_get(worker, "/ping/", timeout=3, debug=False)
            worker.latest_ping_result = "Responding"
            worker.ping_success_at = datetime.datetime.now(tz=tz)
        except requests.exceptions.ConnectTimeout as ex:
            app.logger.info(str(ex))
            worker.latest_ping_result = "Connection Timeout"
        except requests.exceptions.ConnectionError as ex:
            app.logger.info(str(ex))
            worker.latest_ping_result = "Connection Refused"
        except Exception as ex:
            app.logger.info(str(ex))
            worker.latest_ping_result = "Connection Error"
