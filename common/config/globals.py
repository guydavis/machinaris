#
# Common configuration functions.
#

import datetime
import logging
import os
import re
import shutil
import socket
import sqlite3
import time
import traceback
import yaml

from flask import Flask, jsonify, abort, request, flash, g
from stat import S_ISREG, ST_CTIME, ST_MTIME, ST_MODE, ST_SIZE
from subprocess import Popen, TimeoutExpired, PIPE
from os import environ, path

CHIA_BINARY = '/chia-blockchain/venv/bin/chia'
PLOTMAN_CONFIG = '/root/.chia/plotman/plotman.yaml'
PLOTMAN_SAMPLE = '/machinaris/config/plotman.sample.yaml'
PLOTMAN_SCRIPT = '/chia-blockchain/venv/bin/plotman'
MADMAX_BINARY = '/usr/bin/chia_plot'
CHIADOG_PATH = '/chiadog'

RELOAD_MINIMUM_DAYS = 1  # Don't run binaries for version again until this time expires


def load():
    cfg = {}
    cfg['plotting_enabled'] = plotting_enabled()
    cfg['archiving_enabled'] = archiving_enabled()
    cfg['farming_enabled'] = farming_enabled()
    cfg['harvesting_enabled'] = harvesting_enabled()
    cfg['now'] = datetime.datetime.now(tz=None).strftime("%Y-%m-%d %H:%M:%S")
    cfg['machinaris_version'] = load_machinaris_version()
    cfg['machinaris_mode'] = os.environ['mode']
    cfg['chiadog_version'] = load_chiadog_version()
    cfg['plotman_version'] = load_plotman_version()
    cfg['chia_version'] = load_chia_version()
    cfg['madmax_version'] = load_madmax_version()
    cfg['is_controller'] = "localhost" == (
        os.environ['controller_host'] if 'controller_host' in os.environ else 'localhost')
    return cfg


def get_stats_db():
    db = getattr(g, '_stats_database', None)
    if db is None:
        db = g._stats_database = sqlite3.connect(
            '/root/.chia/machinaris/dbs/stats.db')
    return db


def is_setup():
    # First check if plotter and farmer_pk,pool_pk provided.
    if "mode" in os.environ and os.environ['mode'] == 'plotter':
        if "farmer_pk" in os.environ and os.environ['farmer_pk'] != 'null' and \
                "pool_pk" in os.environ and os.environ['pool_pk'] != 'null':
            logging.debug(
                "Found plotter mode with farmer_pk and pool_pk provided.")
            return True  # When plotting don't need private in mnemonic.txt
    if "mode" in os.environ and 'harvester' in os.environ['mode']:
        # Harvester doesn't require a mnemonic private key as farmer's ca already imported.
        return True
    # All other modes, we should have at least one keys path
    if "keys" not in os.environ:
        logging.info(
            "No 'keys' environment variable set for this run. Set an in-container path to mnemonic.txt.")
        return False
    keys = os.environ['keys']
    # logging.debug("Trying with full keys='{0}'".format(keys))
    foundKey = False
    for key in keys.split(':'):
        if os.path.exists(key.strip()):
            # logging.debug("Found key file at: '{0}'".format(key.strip()))
            foundKey = True
        else:
            logging.info("No such keys file: '{0}'".format(key.strip()))
            logging.info(os.listdir(os.path.dirname(key.strip())))
            try:
                logging.info(os.stat(key.strip()))
            except:
                logging.info(traceback.format_exc())
    return foundKey


def get_key_paths():
    if "keys" not in os.environ:
        logging.info(
            "No 'keys' environment variable set for this run. Set an in-container path to mnemonic.txt.")
        return "<UNSET>"
    return os.environ['keys'].split(':')


def farming_enabled():
    return "mode" in os.environ and ("farmer" in os.environ['mode'] or "fullnode" == os.environ['mode'])


def harvesting_enabled():
    return "mode" in os.environ and ("harvester" in os.environ['mode'] or "fullnode" == os.environ['mode'])


def plotting_enabled():
    return "mode" in os.environ and ("plotter" in os.environ['mode'] or "fullnode" == os.environ['mode'])


def archiving_enabled():
    if not plotting_enabled():
        return False
    try:
        with open("/root/.chia/plotman/plotman.yaml") as fp:
            for line in fp.readlines():
                if line.strip().startswith("archiving"):
                    return True
        return False
    except:
        logging.info("Failed to read plotman.yaml so archiving_enabled=False.")
        logging.info(traceback.format_exc())


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
    # Chia version with .dev is actually one # to high
    # See: https://github.com/Chia-Network/chia-blockchain/issues/5655
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
    if not os.path.exists(PLOTMAN_CONFIG):
        logging.info("No existing plotman config found, so copying sample to: {0}" \
                .format(PLOTMAN_CONFIG))
        shutil.copy(PLOTMAN_SAMPLE, PLOTMAN_CONFIG)
    proc = Popen("{0} version".format(PLOTMAN_SCRIPT),
                 stdout=PIPE, stderr=PIPE, shell=True,
                 start_new_session=True, creationflags=0)
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
    if last_plotman_version.endswith('+dev'):
        last_plotman_version = last_plotman_version[:-len('+dev')].strip()
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
                 stdout=PIPE, stderr=PIPE, shell=True, cwd=CHIADOG_PATH)
    try:
        outs, errs = proc.communicate(timeout=90)
    except TimeoutExpired:
        proc.kill()
        proc.communicate()
        abort(500, description="The timeout is expired!")
    if errs:
        abort(500, description=errs.decode('utf-8'))
    last_chiadog_version = outs.decode('utf-8').strip()
    if last_chiadog_version.startswith('v'):
        last_chiadog_version = last_chiadog_version[len('v'):].strip()
    last_chiadog_version_load_time = datetime.datetime.now()
    return last_chiadog_version


last_madmax_version = None
last_madmax_version_load_time = None


def load_madmax_version():
    global last_madmax_version
    global last_madmax_version_load_time
    if last_madmax_version and last_madmax_version_load_time >= \
            (datetime.datetime.now() - datetime.timedelta(days=RELOAD_MINIMUM_DAYS)):
        return last_madmax_version
    proc = Popen("{0} --help".format(MADMAX_BINARY),
                 stdout=PIPE, stderr=PIPE, shell=True)
    try:
        outs, errs = proc.communicate(timeout=90)
    except TimeoutExpired:
        proc.kill()
        proc.communicate()
        abort(500, description="The timeout is expired!")
    if errs:
        abort(500, description=errs.decode('utf-8'))
    last_madmax_version = "?"
    for line in outs.decode('utf-8').splitlines():
        m = re.search(
            r'^Multi-threaded pipelined Chia k32 plotter - (\w+)$', line, flags=re.IGNORECASE)
        if m:
            last_madmax_version = m.group(1)
    last_madmax_version_load_time = datetime.datetime.now()
    return last_madmax_version


last_machinaris_version = None
last_machinaris_version_load_time = None


def load_machinaris_version():
    global last_machinaris_version
    global last_machinaris_version_load_time
    if last_machinaris_version and last_machinaris_version_load_time >= \
            (datetime.datetime.now() - datetime.timedelta(days=RELOAD_MINIMUM_DAYS)):
        return last_machinaris_version
    try:
        with open('/machinaris/VERSION') as version_file:
            last_machinaris_version = version_file.read().strip()
    except:
        logging.info(traceback.format_exc())
        last_machinaris_version = "?"
    last_machinaris_version_load_time = datetime.datetime.now()
    return last_machinaris_version


def get_disks(disk_type):
    if disk_type == "plots":
        try:
            return os.environ['plots_dir'].split(':')
        except:
            logging.info("Unable to find any plots dirs for stats.")
            logging.info(traceback.format_exc())
            return []
    elif disk_type == "plotting":
        try:
            stream = open('/root/.chia/plotman/plotman.yaml', 'r')
            config = yaml.load(stream, Loader=yaml.SafeLoader)
            return config["directories"]["tmp"]
        except:
            logging.info("Unable to find any plotting for stats.")
            logging.info(traceback.format_exc())
            return []
