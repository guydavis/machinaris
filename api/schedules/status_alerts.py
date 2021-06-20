#
# Performs a REST call to controller (possibly localhost) of latest blockchain status.
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
from api.commands import chiadog_cli
from api import app
from api import utils

first_run = True

def update():
    global first_run
    if not globals.farming_enabled() and not globals.harvesting_enabled():
        #app.logger.info("Skipping alerts status collection on plotting-only instance.")
        return
    with app.app_context():
        try:
            hostname = utils.get_hostname()
            if first_run:  # On first launch, load last week of notifications
                since = (datetime.datetime.now() - datetime.timedelta(weeks=1)).strftime("%Y-%m-%d %H:%M:%S.000")
                first_run = False
            else: # On subsequent schedules, load only last 5 minutes.
                since = (datetime.datetime.now() - datetime.timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S.000")
            alerts = chiadog_cli.get_notifications(since)
            payload = []
            for alert in alerts:
                payload.append({
                    "unique_id": hostname + '_' + alert.created_at.strftime("%Y-%m-%d_%H:%M:%S"),
                    "hostname":  hostname,
                    "priority": alert.priority,
                    "service": alert.service,
                    "message": alert.message,
                    "created_at": alert.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                })
            if len(payload) > 0:
                utils.send_post('/alerts/', payload, debug=False)
        except:
            app.logger.info("Failed to load and send alerts status.")
            app.logger.info(traceback.format_exc())
