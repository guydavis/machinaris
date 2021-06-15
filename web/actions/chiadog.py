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

def load_config(farmer):
    return utils.send_get(farmer, "/configs/alerts", debug=False).content

def save_config(farmer, config):
    try: # Validate the YAML first
        yaml.safe_load(config)
    except Exception as ex:
        app.logger.info(traceback.format_exc())
        flash('Updated config.yaml failed validation! Fix and save or refresh page.', 'danger')
        flash(str(ex), 'warning')
    try:
        utils.send_put(farmer, "/configs/alerts", config, debug=True)
    except Exception as ex:
        flash('Failed to save config to farmer.  Please check log files.', 'danger')
        flash(str(ex), 'warning')
    else:
        flash('Nice! Chiadog\'s config.yaml validated and saved successfully.', 'success')

def get_notifications():
    return db.session.query(a.Alert).order_by(a.Alert.created_at.desc()).limit(20).all()

def start_chiadog():
    app.logger.info("Starting Chiadog monitoring....")
    try:
        workdir = "/chiadog"
        configfile = "/root/.chia/chiadog/config.yaml"
        logfile = "/root/.chia/chiadog/logs/chiadog.log"
        log_fd = os.open(logfile, os.O_RDWR|os.O_CREAT)
        log_fo = os.fdopen(log_fd, "a+")
        proc = Popen("/chia-blockchain/venv/bin/python3 -u main.py --config {0}".format(configfile), \
            shell=True, universal_newlines=True, stdout=log_fo, stderr=log_fo, cwd="/chiadog")
    except:
        app.logger.info(traceback.format_exc())
        flash('Failed to start Chiadog monitoring!', 'danger')
        flash('Please see: {0}'.format(logfile), 'warning')
    else:
        flash('Chiadog monitoring started.  Notifications will be sent.', 'success')

def stop_chiadog():
    app.logger.info("Stopping Chiadog monitoring....")
    try:
        os.kill(get_chiadog_pid(), signal.SIGTERM)
    except:
        app.logger.info(traceback.format_exc())
        flash('Failed to stop Chiadog monitoring!', 'danger')
        flash('Please see /root/.chia/chiadog/logs/chiadog.log', 'warning')
    else:
        flash('Chiadog monitoring stopped successfully.  No notifications will be sent!', 'success')
