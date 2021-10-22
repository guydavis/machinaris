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

SUPPORTED_BLOCKCHAINS = [
    'chia',
    'chives',
    'flax',
    'flora',
    'nchain',
    'hddcoin',
]

PLOTMAN_CONFIG = '/root/.chia/plotman/plotman.yaml'
PLOTMAN_SAMPLE = '/machinaris/config/plotman.sample.yaml'

PLOTMAN_SCRIPT = '/chia-blockchain/venv/bin/plotman'
MADMAX_BINARY = '/usr/bin/chia_plot'
BLADEBIT_BINARY = '/usr/bin/bladebit'
CHIADOG_PATH = '/chiadog'

CHIA_BINARY = '/chia-blockchain/venv/bin/chia'
CHIVES_BINARY = '/chives-blockchain/venv/bin/chives'
FLAX_BINARY = '/flax-blockchain/venv/bin/flax'
FLORA_BINARY = '/flora-blockchain/venv/bin/flora'
NCHAIN_BINARY = '/ext9-blockchain/venv/bin/chia'
HDDCOIN_BINARY = '/hddcoin-blockchain/venv/bin/hddcoin'

RELOAD_MINIMUM_DAYS = 1  # Don't run binaries for version again until this time expires

def get_blockchain_binary(blockchain):
    if blockchain == "chia":
        return CHIA_BINARY
    if blockchain == "chives":
        return CHIVES_BINARY
    if blockchain == "flax":
        return FLAX_BINARY
    if blockchain == "flora":
        return FLORA_BINARY
    if blockchain == "nchain":
        return NCHAIN_BINARY
    if blockchain == "hddcoin":
        return HDDCOIN_BINARY
    raise Exception("Invalid blockchain: ".format(blockchain))

def get_blockchain_mainnet(blockchain):
    if blockchain == 'chia':
        return "/root/.chia/mainnet"
    if blockchain == 'chives':
        return "/root/.chives/mainnet"
    if blockchain == 'flax':
        return "/root/.flax/mainnet"
    if blockchain == 'flora':
        return "/root/.flora/mainnet"
    if blockchain == 'hddcoin':
        return "/root/.hddcoin/mainnet"
    if blockchain == 'nchain':
        return "/root/.chia/ext9"

    raise Exception("No mainnet folder for unknown blockchain: {0}".format(blockchain))

def load():
    cfg = {}
    cfg['plotting_enabled'] = plotting_enabled()
    cfg['archiving_enabled'] = archiving_enabled()
    cfg['farming_enabled'] = farming_enabled()
    cfg['harvesting_enabled'] = harvesting_enabled()
    cfg['enabled_blockchains'] = enabled_blockchains()
    cfg['now'] = datetime.datetime.now(tz=None).strftime("%Y-%m-%d %H:%M:%S")
    cfg['machinaris_version'] = load_machinaris_version()
    cfg['machinaris_mode'] = os.environ['mode']
    cfg['plotman_version'] = load_plotman_version()
    cfg['blockchain_version'] = load_blockchain_version(enabled_blockchains()[0])
    cfg['chiadog_version'] = load_chiadog_version()
    cfg['madmax_version'] = load_madmax_version()
    cfg['bladebit_version'] = load_bladebit_version()
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
                (("pool_pk" in os.environ and os.environ['pool_pk'] != 'null') or \
                ("pool_contract_address" in os.environ and os.environ['pool_contract_address'] != 'null')):
            logging.info(
                "Found plotter mode with farmer_pk and pool_pk/pool_contract_address provided.")
        else:
            logging.error(
                "Found plotter mode WITHOUT farmer_pk and pool_pk/pool_contract_address provided.")
        return True  # When plotting don't need private in mnemonic.txt
    if "mode" in os.environ and 'harvester' in os.environ['mode']:
        # Harvester doesn't require a mnemonic private key as farmer's ca already imported.
        return True
    try:
        if os.path.exist(get_blockchain_mainnet(enabled_blockchains()[0]) + '/config/ssl/wallet/public_wallet.key'):
            logging.info("Skipping check for mnemonic.txt as public wallet key exists on disk.")
            return True
    except Exception as ex:
        logging.info("Failed to find presence of public wallet key due to {0}".format(str(ex)))
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

def enabled_blockchains():
    blockchains = []
    if "blockchains" in os.environ:
        for blockchain in os.environ['blockchains'].split():
            if blockchain.lower() in SUPPORTED_BLOCKCHAINS:
                blockchains.append(blockchain.lower())
    return blockchains

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

last_blockchain_version = None
last_blockchain_version_load_time = None
def load_blockchain_version(blockchain):
    chia_binary = get_blockchain_binary(blockchain)
    global last_blockchain_version
    global last_blockchain_version_load_time
    if last_blockchain_version_load_time and last_blockchain_version_load_time >= \
            (datetime.datetime.now() - datetime.timedelta(days=RELOAD_MINIMUM_DAYS)):
        return last_blockchain_version
    last_blockchain_version = ""
    try:
        proc = Popen("{0} version".format(chia_binary),
                stdout=PIPE, stderr=PIPE, shell=True)
        outs, errs = proc.communicate(timeout=90)
        # Chia version with .dev is actually one # to high
        # See: https://github.com/Chia-Network/chia-blockchain/issues/5655
        last_blockchain_version = outs.decode('utf-8').strip()
        if "@@@@" in last_blockchain_version:  # SSL warning 
            try:
                os.system("chia init --fix-ssl-permissions")
            except:
                pass
            last_blockchain_version = ""
        if last_blockchain_version.endswith('dev0'):
            sem_ver = last_blockchain_version.split('.')
            last_blockchain_version = sem_ver[0] + '.' + \
                sem_ver[1] + '.' + str(int(sem_ver[2])-1)
        elif '.dev' in last_blockchain_version:
            sem_ver = last_blockchain_version.split('.')
            last_blockchain_version = sem_ver[0] + '.' + sem_ver[1] + '.' + sem_ver[2]
    except TimeoutExpired:
        proc.kill()
        proc.communicate()
    except:
        logging.info(traceback.format_exc())
    last_blockchain_version_load_time = datetime.datetime.now()
    return last_blockchain_version

last_plotman_version = None
last_plotman_version_load_time = None
def load_plotman_version():
    global last_plotman_version
    global last_plotman_version_load_time
    if last_plotman_version_load_time and last_plotman_version_load_time >= \
            (datetime.datetime.now() - datetime.timedelta(days=RELOAD_MINIMUM_DAYS)):
        return last_plotman_version
    if not os.path.exists(PLOTMAN_CONFIG):
        logging.info("No existing plotman config found, so copying sample to: {0}" \
                .format(PLOTMAN_CONFIG))
        shutil.copy(PLOTMAN_SAMPLE, PLOTMAN_CONFIG)
    last_plotman_version = ""
    try:
        proc = Popen("{0} version".format(PLOTMAN_SCRIPT),
                stdout=PIPE, stderr=PIPE, shell=True,
                start_new_session=True, creationflags=0)
        outs, errs = proc.communicate(timeout=90)
        last_plotman_version = outs.decode('utf-8').strip()
        if last_plotman_version.startswith('plotman'):
            last_plotman_version = last_plotman_version[len('plotman'):].strip()
        #if last_plotman_version.endswith('+dev'):
        #    sem_ver = last_plotman_version.split('.')
        #    last_plotman_version = sem_ver[0] + '.' + sem_ver[1] + '.' + sem_ver[2][:-4]
    except TimeoutExpired:
        proc.kill()
        proc.communicate()
    except:
        logging.info(traceback.format_exc())
    last_plotman_version_load_time = datetime.datetime.now()
    return last_plotman_version

last_chiadog_version = None
last_chiadog_version_load_time = None
def load_chiadog_version():
    global last_chiadog_version
    global last_chiadog_version_load_time
    if last_chiadog_version_load_time and last_chiadog_version_load_time >= \
            (datetime.datetime.now() - datetime.timedelta(days=RELOAD_MINIMUM_DAYS)):
        return last_chiadog_version
    last_chiadog_version = ""
    try:
        proc = Popen("/chia-blockchain/venv/bin/python3 -u main.py --version",
                stdout=PIPE, stderr=PIPE, shell=True, cwd=CHIADOG_PATH)
        outs, errs = proc.communicate(timeout=90)
        last_chiadog_version = outs.decode('utf-8').strip()
        if last_chiadog_version.startswith('v'):
            last_chiadog_version = last_chiadog_version[len('v'):].strip()
        if '-' in last_chiadog_version:
            last_chiadog_version = last_chiadog_version.split('-')[0] + '+dev'
    except TimeoutExpired:
        proc.kill()
        proc.communicate()
    except:
        logging.info(traceback.format_exc())
    last_chiadog_version_load_time = datetime.datetime.now()
    return last_chiadog_version

last_madmax_version = None
last_madmax_version_load_time = None
def load_madmax_version():
    global last_madmax_version
    global last_madmax_version_load_time
    if last_madmax_version_load_time and last_madmax_version_load_time >= \
            (datetime.datetime.now() - datetime.timedelta(days=RELOAD_MINIMUM_DAYS)):
        return last_madmax_version
    last_madmax_version = ""
    try:
        proc = Popen("{0} --help".format(MADMAX_BINARY),
            stdout=PIPE, stderr=PIPE, shell=True)
        outs, errs = proc.communicate(timeout=90)
        for line in outs.decode('utf-8').splitlines():
            m = re.search(
                r'^Multi-threaded pipelined Chia k32 plotter - (\w+)$', line, flags=re.IGNORECASE)
            if m:
                last_madmax_version = m.group(1)
    except TimeoutExpired:
        proc.kill()
        proc.communicate()
    except:
        logging.info(traceback.format_exc())
    last_madmax_version_load_time = datetime.datetime.now()
    return last_madmax_version

last_bladebit_version = None
last_bladebit_version_load_time = None
def load_bladebit_version():
    global last_bladebit_version
    global last_bladebit_version_load_time
    if last_bladebit_version_load_time and last_bladebit_version_load_time >= \
            (datetime.datetime.now() - datetime.timedelta(days=RELOAD_MINIMUM_DAYS)):
        return last_bladebit_version
    last_bladebit_version = ""
    try:
        proc = Popen("{0} --version".format(BLADEBIT_BINARY),
                stdout=PIPE, stderr=PIPE, shell=True)
        outs, errs = proc.communicate(timeout=90)
        last_bladebit_version = outs.decode('utf-8').strip()
        if last_bladebit_version.startswith('v'):
            last_bladebit_version = last_bladebit_version[len('v'):].strip()
        if '-' in last_bladebit_version:
            last_bladebit_version = last_bladebit_version.split('-')[0] + '+dev'
    except TimeoutExpired:
        proc.kill()
        proc.communicate()
    except:
        logging.debug(traceback.format_exc())
    last_bladebit_version_load_time = datetime.datetime.now()
    return last_bladebit_version

last_machinaris_version = None
last_machinaris_version_load_time = None
def load_machinaris_version():
    global last_machinaris_version
    global last_machinaris_version_load_time
    if last_machinaris_version_load_time and last_machinaris_version_load_time >= \
            (datetime.datetime.now() - datetime.timedelta(days=RELOAD_MINIMUM_DAYS)):
        return last_machinaris_version
    last_machinaris_version = ""
    try:
        with open('/machinaris/VERSION') as version_file:
            last_machinaris_version = version_file.read().strip()
    except:
        logging.info(traceback.format_exc())
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
