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
MACHINARIS_VERSION = "0.3.0"

CHIA_BINARY = '/chia-blockchain/venv/bin/chia'
PLOTMAN_SCRIPT = '/chia-blockchain/venv/bin/plotman'

RELOAD_MINIMUM_DAYS = 1  # Don't run binaries for version again until this time expires


def load():
    cfg = {}
    cfg['plotting_only'] = plotting_only()
    cfg['farming_only'] = farming_only()
    cfg['harvesting_only'] = harvesting_only()
    cfg['now'] = datetime.datetime.now(tz=None).strftime("%Y-%m-%d %H:%M:%S")
    cfg['machinaris_version'] = MACHINARIS_VERSION
    cfg['machinaris_mode'] = os.environ['mode']
    cfg['chiadog_version'] = load_chiadog_version()
    cfg['plotman_version'] = load_plotman_version()
    cfg['chia_version'] = load_chia_version()
    return cfg


def is_setup():
    # First check if plotter and farmer_pk,pool_pk provided.
    if "mode" in os.environ and os.environ['mode'] == 'plotter':
        if "farmer_pk" in os.environ and os.environ['farmer_pk'] != 'null' and \
                "pool_pk" in os.environ and os.environ['pool_pk'] != 'null':
            app.logger.debug(
                "Found plotter mode with farmer_pk and pool_pk provided.")
            return True  # When plotting don't need private in mnemonic.txt
    if "mode" in os.environ and os.environ['mode'] == 'harvester':
        # Harvester doesn't require a mnemonic private key as farmer's ca already imported.
        return True
    # All other modes, we should have at least one keys path
    if "keys" not in os.environ:
        app.logger.info(
            "No 'keys' environment variable set for this run. Set an in-container path to mnemonic.txt.")
        return False
    keys = os.environ['keys']
    #app.logger.debug("Trying with full keys='{0}'".format(keys))
    foundKey = False
    for key in keys.split(':'):
        if os.path.exists(key.strip()):
            #app.logger.debug("Found key file at: '{0}'".format(key.strip()))
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
    return "mode" in os.environ and os.environ['mode'] == "farmer"


def harvesting_only():
    return "mode" in os.environ and os.environ['mode'] == "harvester"


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
    # Chia devs use a really weird versioning offset...
    if last_chia_version.endswith('dev0'):
        sem_ver = last_chia_version.split('.')
        last_chia_version = sem_ver[0] + '.' + \
            sem_ver[1] + '.' + str(int(sem_ver[2])-1)
    elif '.dev' in last_chia_version:
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


last_chiadog_version = None
last_chiadog_version_load_time = None


def load_chiadog_version():
    global last_chiadog_version
    global last_chiadog_version_load_time
    if last_chiadog_version and last_chiadog_version_load_time >= \
            (datetime.datetime.now() - datetime.timedelta(days=RELOAD_MINIMUM_DAYS)):
        return last_chiadog_version
    proc = Popen("/chia-blockchain/venv/bin/python3 -u main.py --version",
                 stdout=PIPE, stderr=PIPE, shell=True, cwd="/chiadog")
    try:
        outs, errs = proc.communicate(timeout=90)
    except TimeoutExpired:
        proc.kill()
        proc.communicate()
        abort(500, description="The timeout is expired!")
    if errs:
        abort(500, description=errs.decode('utf-8'))
    last_chiadog_version = outs.decode('utf-8').strip()
    if last_chiadog_version.startswith('chiadog'):
        last_chiadog_version = last_chiadog_version[len('chiadog'):].strip()
    last_chiadog_version_load_time = datetime.datetime.now()
    return last_chiadog_version


def get_disks(disk_type):
    if disk_type == "plots":
        try:
            return os.environ['plots_dir'].split(':')
        except:
            app.logger.info("Unable to find any plots dirs for stats.")
            app.logger.info(traceback.format_exc())
            return []
    elif disk_type == "plotting":
        try:
            stream = open('/root/.chia/plotman/plotman.yaml', 'r')
            config = yaml.load(stream, Loader=yaml.SafeLoader)
            return config["directories"]["tmp"]
        except:
            app.logger.info("Unable to find any plotting for stats.")
            app.logger.info(traceback.format_exc())
            return []
