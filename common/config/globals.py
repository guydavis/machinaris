#
# Common configuration functions.
#

import datetime
import json
import logging
import os
import pathlib
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

from common.utils import converters
from common.models import plottings as pl

PLOTMAN_CONFIG = '/root/.chia/plotman/plotman.yaml'
PLOTMAN_SAMPLE = '/machinaris/config/plotman.sample.yaml'

PLOTMAN_SCRIPT = '/chia-blockchain/venv/bin/plotman'
MADMAX_BINARY = '/usr/bin/chia_plot'
BLADEBIT_BINARY = '/usr/bin/bladebit_cuda'
CHIADOG_PATH = '/chiadog'

RELOAD_MINIMUM_DAYS = 1  # Don't run binaries for version again until this time expires

INFO_FILE = '/machinaris/common/config/blockchains.json'

def get_supported_blockchains():
    try:
        data = json.load(open(INFO_FILE))
        return sorted(data.keys())
    except:
        raise Exception("No blockchain info found at {0}.".format(INFO_FILE))

def get_blockchain_binary(blockchain):
    return load_blockchain_info(blockchain, 'binary')

def get_blockchain_working_dir(blockchain):
    if blockchain == 'gigahorse':
        return os.path.dirname(get_blockchain_binary(blockchain))
    return None # Default for other blockchains that are cwd-independent

def get_blockchain_network_path(blockchain):
    return load_blockchain_info(blockchain, 'network_path')

def get_blockchain_network_name(blockchain):
    return load_blockchain_info(blockchain, 'network_name')

def get_blockchain_symbol(blockchain):
    return load_blockchain_info(blockchain, 'symbol')

def get_blockchain_network_port(blockchain):
    return load_blockchain_info(blockchain, 'network_port')

def get_full_node_rpc_port(blockchain):
    return load_blockchain_info(blockchain, 'fullnode_rpc_port')

def get_blocks_per_day(blockchain):
    return load_blockchain_info(blockchain, 'blocks_per_day')

def get_block_reward(blockchain):
    return load_blockchain_info(blockchain, 'reward')

def get_mojos_per_coin(blockchain):
    return load_blockchain_info(blockchain, 'mojos_per_coin')

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
    cfg['blockchain_version'] = load_blockchain_version(cfg['enabled_blockchains'][0])
    cfg['chiadog_version'] = load_chiadog_version()
    cfg['madmax_version'] = load_madmax_version()
    cfg['bladebit_version'] = load_bladebit_version()
    cfg['is_controller'] = "localhost" == (
        os.environ['controller_host'] if 'controller_host' in os.environ else 'localhost')
    fullnode_db_version = load_fullnode_db_version()
    if fullnode_db_version:
        cfg['fullnode_db_version'] = fullnode_db_version
    if 'fullnode' in cfg['machinaris_mode']:
        cfg['wallet_status'] = "running" if wallet_running() else "paused"
        if cfg['enabled_blockchains'][0] == 'mmx':
            cfg['mmx_reward'] = gather_mmx_reward()
    return cfg

def load_blockchain_info(blockchain, key):
    try:
        data = json.load(open(INFO_FILE))
        if blockchain in data:
            if key in data[blockchain]:
                return data[blockchain][key]
            else:
                raise Exception("Blockchain info key not found for {0}/{1}".format(blockchain, key))
        else:
            raise Exception("Blockchain info not found for {0}/{1}".format(blockchain, key))
    except:
        raise Exception("No blockchain info found at {0} for {1}/{2}".format(INFO_FILE, blockchain, key))

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
    # All other modes, we should have at least one keys path
    if "keys" not in os.environ:
        logging.info(
            "No 'keys' environment variable set for this run. Set an in-container path to mnemonic.txt.")
        return False
    keys = os.environ['keys']
    # logging.debug("Trying with full keys='{0}'".format(keys))
    foundKey = False
    for key in keys.split(':'):
        if key.strip() == "persistent":  # User wants to manage themselves
            return True # pretend a key was found
        if os.path.exists(key.strip()) and os.path.getsize(key.strip()) > 0:
            # logging.debug("Found key file at: '{0}'".format(key.strip()))
            foundKey = True
        else:
            logging.info("No such key file with mnemonic: '{0}'".format(key.strip()))
            logging.info(os.listdir(os.path.dirname(key.strip())))
            try:
                logging.info(os.stat(key.strip()))
            except:
                logging.info(traceback.format_exc())
    return foundKey

# On very first launch of the main Chia container, blockchain DB gz is being downloaded via torrent so must wait.
CHIA_COMPRESSED_DB_SIZE = 75 * 1024 * 1024 * 1024 # Compressed GB in March 2024
CHIA_BLOCKCHAIN_DB_SIZE = 127 * 1024 * 1024 * 1024 # Uncompressed GB in March 2024
def blockchain_downloading():
    db_path = '/root/.chia/mainnet/db'
    if path.exists(f"{db_path}/blockchain_v1_mainnet.sqlite") or path.exists(f"{db_path}/blockchain_v2_mainnet.sqlite"):
        return [100, None]
    tmp_path =  f"{db_path}/chia"
    if not path.exists(tmp_path):
        logging.info("No folder at {0} yet...".format(tmp_path))
        return [0, "0 GB"]
    target_size = CHIA_COMPRESSED_DB_SIZE + CHIA_BLOCKCHAIN_DB_SIZE
    if path.exists(db_path + '/chia/.chiadb_decompressed_on_the_fly'): # If decompressed via pipe from download
        target_size = CHIA_BLOCKCHAIN_DB_SIZE
    # Chia and Gigahorse download via libtorrent that allocates full file size before any downloading, so use status file
    if path.exists(db_path + '/chia/.chiadb_download_size'):
        with open(db_path + '/chia/.chiadb_download_size',"r") as f:
            bytes = int(f.read())
    else: # Later when decompressing, just read file sizes on disk
        bytes = sum(f.stat().st_size for f in pathlib.Path(tmp_path).glob('**/*') if f.is_file())
    return [ round(100*bytes/(target_size), 2), converters.convert_size(bytes) ]

def get_key_paths():
    if "keys" not in os.environ:
        logging.info(
            "No 'keys' environment variable set for this run. Set an in-container path to mnemonic.txt.")
        return "<UNSET>"
    return os.environ['keys'].split(':')

def farming_enabled():
    return "mode" in os.environ and ("farmer" in os.environ['mode'] or "fullnode" in os.environ['mode'])

def harvesting_enabled():
    return "mode" in os.environ and ("harvester" in os.environ['mode'] or "fullnode" in os.environ['mode'])

def plotting_enabled():
    return "mode" in os.environ and ("plotter" in os.environ['mode'] or "fullnode" in os.environ['mode']) \
        and enabled_blockchains()[0] in pl.PLOTTABLE_BLOCKCHAINS

def enabled_blockchains():
    supported_blockchains = get_supported_blockchains()
    blockchains = []
    if "blockchains" in os.environ:
        for blockchain in os.environ['blockchains'].split():
            if blockchain.lower() in supported_blockchains:
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

# Ignore error at CLI about "data_layer.crt" that is still NOT fixed, despite being "closed".
# https://github.com/Chia-Network/chia-blockchain/issues/13257
def strip_data_layer_msg(lines):
    useful_lines = []
    for line in lines:
        if "data_layer.crt" in line:
            pass
        else:
            useful_lines.append(line)
    return useful_lines

last_blockchain_version = None
last_blockchain_version_load_time = None
def load_blockchain_version(blockchain):
    if blockchain == 'mmx':
        return "recent" # Author didn't bother to version his binaries
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
        last_blockchain_version = strip_data_layer_msg(outs.decode('utf-8').strip().splitlines())[0]
        if "@@@@" in last_blockchain_version:  # SSL warning 
            try:
                os.system("chia init --fix-ssl-permissions")
            except:
                pass
            last_blockchain_version = ""
        if last_blockchain_version.endswith('dev0') or last_blockchain_version.endswith('dev1'):
            if 'rc' in last_blockchain_version: # Strip out 'rcX' if found.
                last_blockchain_version = last_blockchain_version[:last_blockchain_version.index('rc')]
            elif 'b1' in last_blockchain_version: # Strip out 'b1' if found.
                last_blockchain_version = last_blockchain_version[:last_blockchain_version.index('b1')]
            elif 'b2' in last_blockchain_version: # Strip out 'b2' if found.
                last_blockchain_version = last_blockchain_version[:last_blockchain_version.index('b2')]
            elif 'b3' in last_blockchain_version: # Strip out 'b3' if found.
                last_blockchain_version = last_blockchain_version[:last_blockchain_version.index('b3')]
            else:
                # Chia version with .dev is actually one # to high, never fixed by Chia team...
                # See: https://github.com/Chia-Network/chia-blockchain/issues/5655
                sem_ver = last_blockchain_version.split('.')
                last_blockchain_version = sem_ver[0] + '.' + sem_ver[1] + '.' + str(int(sem_ver[2])-1)
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
    if not os.path.exists(PLOTMAN_SCRIPT):
        return ""
    if last_plotman_version_load_time and last_plotman_version_load_time >= \
            (datetime.datetime.now() - datetime.timedelta(days=RELOAD_MINIMUM_DAYS)):
        return last_plotman_version
    if not os.path.exists(PLOTMAN_CONFIG):
        try:
            logging.info("No existing plotman config found, so copying sample to: {0}" \
                .format(PLOTMAN_CONFIG))
            shutil.copy(PLOTMAN_SAMPLE, PLOTMAN_CONFIG)
        except:
            pass
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
        logging.error(traceback.format_exc())
    last_plotman_version_load_time = datetime.datetime.now()
    return last_plotman_version

last_chiadog_version = None
last_chiadog_version_load_time = None
def load_chiadog_version():
    global last_chiadog_version
    global last_chiadog_version_load_time
    if not os.path.exists(CHIADOG_PATH):
        return ""
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
        logging.error(traceback.format_exc())
    last_chiadog_version_load_time = datetime.datetime.now()
    return last_chiadog_version

last_madmax_version = None
last_madmax_version_load_time = None
def load_madmax_version():
    global last_madmax_version
    global last_madmax_version_load_time
    if not os.path.exists(MADMAX_BINARY):
        return ""
    if last_madmax_version_load_time and last_madmax_version_load_time >= \
            (datetime.datetime.now() - datetime.timedelta(days=RELOAD_MINIMUM_DAYS)):
        return last_madmax_version
    last_madmax_version = ""
    try:
        proc = Popen("{0} --version".format(MADMAX_BINARY),
            stdout=PIPE, stderr=PIPE, shell=True)
        outs, errs = proc.communicate(timeout=90)  # Example: 1.1.8-d1a9e88
        last_madmax_version = outs.decode('utf-8').strip().split('-')[0]
    except TimeoutExpired:
        proc.kill()
        proc.communicate()
    except:
        logging.error(traceback.format_exc())
    last_madmax_version_load_time = datetime.datetime.now()
    return last_madmax_version

last_bladebit_version = None
last_bladebit_version_load_time = None
def load_bladebit_version():
    global last_bladebit_version
    global last_bladebit_version_load_time
    if not os.path.exists(BLADEBIT_BINARY):
        return ""
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

fullnode_db_version = None
fullnode_db_version_load_time = None
def load_fullnode_db_version():
    global fullnode_db_version
    global fullnode_db_version_load_time
    if fullnode_db_version_load_time and fullnode_db_version_load_time >= \
            (datetime.datetime.now() - datetime.timedelta(days=RELOAD_MINIMUM_DAYS)):
        return fullnode_db_version
    fullnode_db_version = None
    blockchain = enabled_blockchains()[0]
    v1_db_file = get_blockchain_network_path(blockchain) + '/db/blockchain_v1_mainnet.sqlite'
    v2_db_file = get_blockchain_network_path(blockchain) + '/db/blockchain_v2_mainnet.sqlite'
    try:
        if os.path.exists(v2_db_file):
            return "v2"
        elif os.path.exists(v1_db_file):
            return "v1"
    except:
        logging.info(traceback.format_exc())
    fullnode_db_version_load_time = datetime.datetime.now()
    return fullnode_db_version

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

def get_alltheblocks_name(blockchain):
    if blockchain == 'staicoin':
        return 'stai' # Special case for staicoin's inconsistent naming convention
    elif blockchain == 'gigahorse':
        return 'chia' # Special case for gigahorse which is really Chia
    return blockchain

def legacy_blockchain(blockchain):
    return blockchain in ['achi', 'ballcoin', 'coffee', 'ecostake', 'gold', 'mint', 'nchain', 'petroleum', 'profit', 'silicoin', 'stor']

last_mmx_reward = None
last_mmx_reward_load_time = None
def gather_mmx_reward():
    mmx_binary = get_blockchain_binary('mmx')
    global last_mmx_reward
    global last_mmx_reward_load_time
    if last_mmx_reward_load_time and last_mmx_reward_load_time >= \
            (datetime.datetime.now() - datetime.timedelta(minutes=15)):
        return last_mmx_reward
    last_mmx_reward = ""
    try:
        proc = Popen("{0} node info | grep -i reward".format(mmx_binary),
                stdout=PIPE, stderr=PIPE, shell=True)
        outs, errs = proc.communicate(timeout=90)
        reward_line = outs.decode('utf-8').strip()
        if reward_line.startswith("Reward:"):
            # Example -> "Reward:   0.439271 MMX"
            last_mmx_reward = reward_line.split(':')[1][:-3].strip()
    except TimeoutExpired:
        proc.kill()
        proc.communicate()
    except:
        logging.error(traceback.format_exc())
    last_mmx_reward_load_time = datetime.datetime.now()
    return last_mmx_reward

def wallet_running():
    blockchain = enabled_blockchains()[0]
    if blockchain == 'mmx':
        return True # Always running for MMX
    if blockchain == 'gigahorse':
        chia_binary_short = 'chia' # wallet process is 'chia_wallet'
    else:
        chia_binary_short = get_blockchain_binary(blockchain).split('/')[-1]
    try:
        cmd = "pidof {0}_wallet".format(chia_binary_short)
        proc = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
        outs, errs = proc.communicate(timeout=90)
        pid = outs.decode('utf-8').strip()
        #print("{0} --> {1}".format(cmd, pid))
        if pid:
            return True
        else:
            return False
    except TimeoutExpired:
        proc.kill()
        proc.communicate()
    except:
        logging.error(traceback.format_exc())
    return False

def get_container_memory_usage_bytes():
    try: # Check cgroups v1
        with open("/sys/fs/cgroup/memory/memory.usage_in_bytes", "r") as f:
            return int(f.readline())
    except Exception as ex:
        pass
    try: # Check cgroups v2
        with open("/sys/fs/cgroup/memory.current", "r") as f:
            return int(f.readline())
    except Exception as ex:
        pass
    return None

def get_host_memory_usage_percent():
    try:
        total_mem = None
        avail_mem = None
        with open("/proc/meminfo", "r") as f:
            for line in f.readlines():
                if line.startswith('MemTotal:'):
                    #logging.error("{0} -> {1}".format(line, line.split(':')[1].strip().split(' ')[0]))
                    total_mem = int(line.split(':')[1].strip().split(' ')[0])
                elif line.startswith('MemAvailable:'):
                    #logging.error("{0} -> {1}".format(line, line.split(':')[1].strip().split(' ')[0]))
                    avail_mem = int(line.split(':')[1].strip().split(' ')[0])
        if total_mem and avail_mem:
            return 100 - int(avail_mem / total_mem * 100)  # Used memory percentage
    except Exception as ex:
        logging.error("Failed to calculate total host memory usage percentage due to: {0}".format(str(ex)))
    return None
