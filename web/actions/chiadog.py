#
# CLI interactions with the chiadog script.
#

import datetime
import os
import psutil
import signal
import shutil
import sqlite3
import time
import traceback
import yaml

from flask import Flask, jsonify, abort, request, flash, g
from subprocess import Popen, TimeoutExpired, PIPE

from common.models import alerts as a
from web import app, db, utils
from . import worker as wk

def load_config(farmer):
    return utils.send_get(farmer, "/configs/alerts", debug=False).content

def load_farmers():
    worker_summary = wk.load_worker_summary()
    farmers = []
    for farmer in worker_summary.workers:
        if (farmer in worker_summary.farmers) or (farmer in worker_summary.harvesters):
            farmers.append({
                'hostname': farmer.hostname,
                'monitoring_status': farmer.monitoring_status().lower()
            })
    return farmers

def save_config(farmer, config):
    try: # Validate the YAML first
        yaml.safe_load(config)
    except Exception as ex:
        app.logger.info(traceback.format_exc())
        flash('Updated config.yaml failed validation! Fix and save or refresh page.', 'danger')
        flash(str(ex), 'warning')
    try:
        utils.send_put(farmer, "/configs/alerts", config, debug=False)
    except Exception as ex:
        flash('Failed to save config to farmer.  Please check log files.', 'danger')
        flash(str(ex), 'warning')
    else:
        flash('Nice! Chiadog\'s config.yaml validated and saved successfully.', 'success')

def get_notifications():
    return db.session.query(a.Alert).order_by(a.Alert.created_at.desc()).limit(20).all()

def start_chiadog(farmer):
    app.logger.info("Starting Chiadog monitoring...")
    try:
        utils.send_post(farmer, "/actions/", {"service": "monitoring","action": "start"}, debug=False)
    except:
        app.logger.info(traceback.format_exc())
        flash('Failed to start Chiadog monitoring!', 'danger')
        flash('Please see log files.', 'warning')
    else:
        flash('Chiadog monitoring started.  Notifications will be sent.', 'success')

def stop_chiadog(farmer):
    app.logger.info("Stopping Chiadog monitoring...")
    try:
        utils.send_post(farmer, "/actions/", payload={"service": "monitoring","action": "stop"}, debug=False)
    except:
        app.logger.info(traceback.format_exc())
        flash('Failed to stop Chiadog monitoring!', 'danger')
        flash('Please see log files.', 'warning')
    else:
        flash('Chiadog monitoring stopped successfully.  No notifications will be sent!', 'success')
