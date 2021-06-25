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

def load_config():
    return open('/root/.chia/chiadog/config.yaml','r').read()

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
        raise Exception('Updated config.yaml failed validation!\n' + str(ex))
    else:
        if get_chiadog_pid():
            stop_chiadog()
            start_chiadog()

def get_chiadog_pid():
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        if proc.info['name'] == 'python3' and '/root/.chia/chiadog/config.yaml' in proc.info['cmdline']:
            return proc.info['pid']
    return None

def get_notifications(since):
    return chiadog.Notification.query.filter(chiadog.Notification.created_at >= since). \
        order_by(chiadog.Notification.created_at.desc()).limit(20).all()

def dispatch_action(job):
    service = job['service']
    if service != 'monitoring':
        raise Exception("Only monitoring jobs handled here!")
    action = job['action']
    if action == "start":
        start_chiadog()
    elif action == "stop":
        stop_chiadog()
    elif action == "restart":
        stop_chiadog()
        time.sleep(5)
        start_chiadog()
    else:
        raise Exception("Unsupported action {0} for monitoring.".format(action))

def start_chiadog():
    #app.logger.info("Starting Chiadog monitoring....")
    try:
        workdir = "/chiadog"
        configfile = "/root/.chia/chiadog/config.yaml"
        logfile = "/root/.chia/chiadog/logs/chiadog.log"
        proc = Popen("nohup /chia-blockchain/venv/bin/python3 -u main.py --config {0} >> {1} 2>&1 &".format(configfile, logfile), \
            shell=True, universal_newlines=True, stdout=None, stderr=None, cwd="/chiadog")
    except:
        app.logger.info('Failed to start Chiadog monitoring!')
        app.logger.info(traceback.format_exc())

def stop_chiadog():
    #app.logger.info("Stopping Chiadog monitoring....")
    try:
        os.kill(get_chiadog_pid(), signal.SIGTERM)
    except:
        app.logger.info('Failed to stop Chiadog monitoring!')
        app.logger.info(traceback.format_exc())
