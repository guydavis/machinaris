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

from api.models import chiadog
from api import app

def save_config(config):
    try:
        # Validate the YAML first
        yaml.safe_load(config)
        # Save a copy of the old config file
        src="/root/.chia/chiadog/config.yaml"
        dst="/root/.chia/chiadog/config.yaml."+time.strftime("%Y%m%d-%H%M%S")+".yaml"
        shutil.copy(src,dst)
        # Now save the new contents to main config file
        with open(src, 'w') as writer:
            writer.write(config)
    except Exception as ex:
        app.logger.info(traceback.format_exc())
        flash('Updated config.yaml failed validation! Fix and save or refresh page.', 'danger')
        flash(str(ex), 'warning')
    else:
        flash('Nice! Chiadog\'s config.yaml validated and saved successfully.', 'success')
        if get_chiadog_pid():
            flash('NOTE: Please restart Chiadog on the Alerts page to pickup your changes.', 'info')

def get_chiadog_pid():
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        if proc.info['name'] == 'python3' and '/root/.chia/chiadog/config.yaml' in proc.info['cmdline']:
            return proc.info['pid']
    return None

def get_notifications(since):
    return chiadog.Notification.query.filter(chiadog.Notification.created_at >= since). \
        order_by(chiadog.Notification.created_at.desc()).limit(20).all()

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
