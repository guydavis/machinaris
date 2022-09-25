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

from common.models import alerts as a
from common.config import globals
from api.commands import chiadog_cli
from api import app, utils

DELETE_OLD_STATS_AFTER_DAYS = 3  # Keep at most 3 days of old alerts

first_run = True

def delete_old_alerts(db):
    try:
        cutoff = datetime.datetime.now() - datetime.timedelta(days=DELETE_OLD_STATS_AFTER_DAYS)
        db.session.query(a.Alert).filter(a.Alert.created_at <= cutoff).delete()
        db.session.commit()
        app.logger.debug("Deleted old alerts before {0}".format(cutoff.strftime("%Y-%m-%d %H:%M")))
    except:
        app.logger.info("Failed to delete old alerts.")
        app.logger.info(traceback.format_exc())

def update():
    global first_run
    with app.app_context():
        try:
            from api import db
            delete_old_alerts(db)
            if globals.load()['is_controller']:
                #app.logger.info("Skipping alerts polling on fullnode are already placed in database directly via chiadog_notifier.sh script.")
                return
            hostname = utils.get_hostname()
            if first_run:  # On first launch, load last hour of notifications
                since = (datetime.datetime.now() - datetime.timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
                first_run = False
            else: # On subsequent schedules, load only last 15 minutes.
                since = (datetime.datetime.now() - datetime.timedelta(minutes=15)).strftime("%Y-%m-%d %H:%M:%S")
            alerts = db.session.query(a.Alert).filter(a.Alert.created_at >= since).order_by(a.Alert.created_at.desc()).limit(20).all()
            payload = []
            for alert in alerts:
                payload.append({
                    "unique_id": hostname + '_{0}_'.format(alert.blockchain) + \
                            alert.created_at.strftime("%Y-%m-%d_%H:%M:%S"),
                    "hostname":  hostname,
                    "blockchain": alert.blockchain,
                    "priority": alert.priority,
                    "service": alert.service,
                    "message": alert.message,
                    "created_at": alert.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                })
            if len(payload) > 0:
                utils.send_post('/alerts/', payload, debug=False)
        except Exception as ex:
            app.logger.info("Failed to load and send alerts status because {0}".format(str(ex)))
