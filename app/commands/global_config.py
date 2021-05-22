#
# Common configuration functions.
#

import datetime
import os
import shutil
import socket
import time
import traceback
import yaml

from flask import Flask, jsonify, abort, request, flash
from stat import S_ISREG, ST_CTIME, ST_MTIME, ST_MODE, ST_SIZE
from subprocess import Popen, TimeoutExpired, PIPE
from os import path

from app import app
from app.models import chia
from app.commands import global_config

# Hard-coded verson numbers for now
MACHINARIS_VERSION="0.3.0"
CHIADOG_VERSION="0.5.1" # See https://github.com/martomi/chiadog/releases

CHIA_BINARY = '/chia-blockchain/venv/bin/chia'
PLOTMAN_SCRIPT = '/chia-blockchain/venv/bin/plotman'

RELOAD_MINIMUM_DAYS = 1 # Don't run binaries for version again until this time expires

def load():
    cfg = {}
    cfg['plotting_only'] = plotting_only()
    cfg['farming_only'] = farming_only()
    cfg['now'] = datetime.datetime.now(tz=None).strftime("%Y-%m-%d %H:%M:%S")
    cfg['machinaris_version'] = MACHINARIS_VERSION
    cfg['chiadog_version'] = CHIADOG_VERSION
    cfg['plotman_version'] = load_plotman_version()
    cfg['chia_version'] = load_chia_version()
    return cfg

def is_setup():
    if "keys" not in os.environ:
        app.logger.info(
            "No 'keys' environment variable set for this run. Set an in-container path to mnemonic.txt.")
        return False
    keys = os.environ['keys']
    app.logger.debug("Trying with full keys='{0}'".format(keys))
    foundKey = False
    for key in keys.split(':'):
        if os.path.exists(key.strip()):
            app.logger.debug("Found key file at: '{0}'".format(key.strip()))
            foundKey = True
        else:
            app.logger.info("No such keys file: '{0}'".format(key.strip()))
            app.logger.info(os.listdir(os.path.dirname(key.strip())))
            try:
                app.logger.info(os.stat(key.strip()))
            except:
                app.logger.info(traceback.format_exc())
    return foundKey

def get_key_paths():
    if "keys" not in os.environ:
        app.logger.info(
            "No 'keys' environment variable set for this run. Set an in-container path to mnemonic.txt.")
        return "<UNSET>"
    return os.environ['keys'].split(':')

def plotting_only():
    return "mode" in os.environ and os.environ['mode'] == "plotter"

def farming_only():
    return "mode" in os.environ and os.environ['mode'] in ["harvester", "farmer"]

last_chia_version = None
last_chia_version_load_time = None

def load_chia_version():
    global last_chia_version
    global last_chia_version_load_time
    if last_chia_version and last_chia_version_load_time >= \
            (datetime.datetime.now() - datetime.timedelta(days=RELOAD_MINIMUM_DAYS)):
        return last_chia_version
    proc = Popen("{0} version".format(CHIA_BINARY),
                 stdout=PIPE, stderr=PIPE, shell=True)
    try:
        outs, errs = proc.communicate(timeout=90)
    except TimeoutExpired:
        proc.kill()
        proc.communicate()
        abort(500, description="The timeout is expired!")
    if errs:
        abort(500, description=errs.decode('utf-8'))
    last_chia_version = outs.decode('utf-8').strip()
    if '.dev' in last_chia_version:
        sem_ver = last_chia_version.split('.')
        last_chia_version = sem_ver[0] + '.' + sem_ver[1] + '.' + sem_ver[2]
    last_chia_version_load_time = datetime.datetime.now()
    return last_chia_version

last_plotman_version = None
last_plotman_version_load_time = None

def load_plotman_version():
    global last_plotman_version
    global last_plotman_version_load_time
    if last_plotman_version and last_plotman_version_load_time >= \
            (datetime.datetime.now() - datetime.timedelta(days=RELOAD_MINIMUM_DAYS)):
        return last_plotman_version
    proc = Popen("{0} version < /dev/tty".format(PLOTMAN_SCRIPT),
                 stdout=PIPE, stderr=PIPE, shell=True)
    try:
        outs, errs = proc.communicate(timeout=90)
    except TimeoutExpired:
        proc.kill()
        proc.communicate()
        abort(500, description="The timeout is expired!")
    if errs:
        abort(500, description=errs.decode('utf-8'))
    last_plotman_version = outs.decode('utf-8').strip()
    if last_plotman_version.startswith('plotman'):
        last_plotman_version = last_plotman_version[len('plotman'):].strip()
    last_plotman_version_load_time = datetime.datetime.now()
    return last_plotman_version
