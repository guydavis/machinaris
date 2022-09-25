#
# CLI interactions with the chia binary.
#

import asyncio
import datetime
import json
import os
import pexpect
import psutil
import re
import signal
import shutil
import socket
import time
import traceback
import yaml

from flask import Flask, jsonify, abort, request, flash
from flask_babel import _, lazy_gettext as _l
from stat import S_ISREG, ST_CTIME, ST_MTIME, ST_MODE, ST_SIZE
from subprocess import Popen, TimeoutExpired, PIPE, STDOUT
from os import path

from common.config import globals
from api import app
from api.models import chia
from api.commands import websvcs

# When reading tail of chia plots check output, limit to this many lines
MAX_LOG_LINES = 2000

# When this file present, we are leaving wallet paused normally, syncing every day or so
WALLET_SETTINGS_FILE = '/root/.chia/machinaris/config/wallet_settings.json'

def load_farm_summary(blockchain):
    chia_binary = globals.get_blockchain_binary(blockchain)
    if globals.farming_enabled():
        proc = Popen("{0} farm summary".format(chia_binary), stdout=PIPE, stderr=PIPE, shell=True)
        try:
            outs, errs = proc.communicate(timeout=30)
            if errs:
                app.logger.error("Error from {0} farm summary because {1}".format(blockchain, outs.decode('utf-8')))
        except TimeoutExpired:
            proc.kill()
            proc.communicate()
            raise Exception("For farm summary, the process timeout expired!")
        return chia.FarmSummary(globals.strip_data_layer_msg(outs.decode('utf-8').splitlines()), blockchain)
    elif globals.harvesting_enabled():
        return chia.HarvesterSummary()
    else:
        raise Exception("Unable to load farm summary on non-farmer and non-harvester.")

def load_config(blockchain):
    mainnet = globals.get_blockchain_network_path(blockchain)
    return open(f'{mainnet}/config/config.yaml','r').read()

def save_config(config, blockchain):
    try:
        # Validate the YAML first
        yaml.safe_load(config)
        # Save a copy of the old config file
        mainnet = globals.get_blockchain_network_path(blockchain)
        src=f'{mainnet}/config/config.yaml'
        dst=f'{mainnet}/config/config.' + time.strftime("%Y%m%d-%H%M%S")+".yaml"
        shutil.copy(src,dst)
        # Now save the new contents to main config file
        with open(src, 'w') as writer:
            writer.write(config)
    except Exception as ex:
        app.logger.info(traceback.format_exc())
        raise Exception(_('Updated config.yaml failed validation!') + '\n' + str(ex))
    else:
        try:
            restart_farmer(blockchain)
        except Exception as ex:
            app.logger.info("Failed to restart farmer because {0}.".format(str(ex)))

def load_wallet_show(blockchain):
    if not globals.wallet_running():
        return None
    chia_binary = globals.get_blockchain_binary(blockchain)
    wallet_show = ""
    child = pexpect.spawn("{0} wallet show".format(chia_binary))
    wallet_id_num = app.config['SELECTED_WALLET_NUM']  # Default wallet ID num to respond if prompted is 1
    app.logger.debug("Default SELECTED_WALLET_NUM is {0}".format(wallet_id_num))
    while True:
        i = child.expect(["Wallet height:.*\r\n", "Wallet keys:.*\r\n", "Choose wallet key:.*\r\n", 
            "Choose a wallet key:.*\r\n", "No online backup file found.*\r\n", "Connection error.*\r\n"], timeout=90)
        if i == 0:
            app.logger.debug("wallet show returned 'Wallet height...' so collecting details.")
            wallet_show += child.after.decode("utf-8") + child.before.decode("utf-8") + child.read().decode("utf-8")
            break
        elif i == 1 or i == 2 or i == 3:
            app.logger.info("Wallet show got num prompt so selecting wallet #{0}".format(wallet_id_num))
            child.sendline("{0}".format(wallet_id_num))
        elif i == 4:
            child.sendline("S")
        elif i == 5:
            raise Exception("Skipping wallet status gathering as it returned 'Connection Error', so possibly still starting up. If this error persists more than 30 minutes after startup, try restarting the Machinaris Docker container.")
        else:
            raise Exception("ERROR:\n" + child.after.decode("utf-8") + child.before.decode("utf-8") + child.read().decode("utf-8"))
    return chia.Wallet(wallet_show)

def load_blockchain_show(blockchain):
    chia_binary = globals.get_blockchain_binary(blockchain)
    proc = Popen("{0} show --state".format(chia_binary), stdout=PIPE, stderr=PIPE, shell=True)
    try:
        outs, errs = proc.communicate(timeout=30)
        if errs:
            raise Exception(errs.decode('utf-8'))
    except TimeoutExpired:
        proc.kill()
        proc.communicate()
        raise Exception("For blockchain show, the process timeout expired!")
    return chia.Blockchain(globals.strip_data_layer_msg(outs.decode('utf-8').splitlines()))

def load_connections_show(blockchain):
    chia_binary = globals.get_blockchain_binary(blockchain)
    if blockchain in ['cactus', 'maize']:  # Cactus & Maize now supports only 'peer' command
        proc = Popen("{0} peer -c full_node".format(chia_binary), stdout=PIPE, stderr=PIPE, shell=True)
    else:
        proc = Popen("{0} show --connections".format(chia_binary), stdout=PIPE, stderr=PIPE, shell=True)
    try:
        outs, errs = proc.communicate(timeout=30)
        if errs:
            raise Exception(errs.decode('utf-8'))
    except TimeoutExpired:
        proc.kill()
        proc.communicate()
        raise Exception("For connections show, the process timeout expired!")
    return chia.Connections(globals.strip_data_layer_msg(outs.decode('utf-8').splitlines()))

def load_keys_show(blockchain):
    chia_binary = globals.get_blockchain_binary(blockchain)
    # If a legacy blockchain that hasn't kept pace with Chia, there is only non-observer key
    if globals.legacy_blockchain(blockchain):
        proc = Popen("{0} keys show".format(chia_binary), stdout=PIPE, stderr=PIPE, shell=True)
    else: # Get both observer and non-observer keys for newer blockchains
        proc = Popen("{0} keys show && {0} keys show -d | grep 'non-observer'".format(chia_binary), stdout=PIPE, stderr=PIPE, shell=True)
    try:
        outs, errs = proc.communicate(timeout=30)
        if errs:
            raise Exception(errs.decode('utf-8'))
    except TimeoutExpired:
        proc.kill()
        proc.communicate()
        raise Exception("For keys show, the process timeout expired!")
    return chia.Keys(globals.strip_data_layer_msg(outs.decode('utf-8').splitlines()))

def restart_farmer(blockchain):
    chia_binary = globals.get_blockchain_binary(blockchain)
    if os.path.exists(WALLET_SETTINGS_FILE):
        cmd = "{0} stop farmer && {0} start farmer-no-wallet".format(chia_binary)
    else:
        cmd = "{0} start farmer && {0} start farmer -r".format(chia_binary)
    app.logger.info("Executing farmer restart: {0}".format(cmd))
    proc = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
    try:
        outs, errs = proc.communicate(timeout=90)
        if errs:
            app.logger.error("{0}".format(errs.decode('utf-8')))
            return False
    except TimeoutExpired as ex:
        proc.kill()
        proc.communicate()
        app.logger.error(traceback.format_exc())
        return False
    return True

def start_wallet(blockchain):
    chia_binary = globals.get_blockchain_binary(blockchain)
    cmd = "{0} start wallet -r".format(chia_binary)
    app.logger.info("Executing wallet start: {0}".format(cmd))
    proc = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
    try:
        outs, errs = proc.communicate(timeout=90)
        if errs:
            app.logger.error("{0}".format(errs.decode('utf-8')))
            return False
    except TimeoutExpired as ex:
        proc.kill()
        proc.communicate()
        app.logger.error(traceback.format_exc())
        return False
    return True

def pause_wallet(blockchain):
    chia_binary = globals.get_blockchain_binary(blockchain)
    if globals.legacy_blockchain(blockchain):  # Old chains will stop fullnode(!) if ask to stop just the wallet...
        cmd = "{0} stop farmer && {0} start farmer-no-wallet".format(chia_binary)
    else:  # Updated blockchains can simply stop the wallet
        cmd = "{0} stop wallet".format(chia_binary)
    app.logger.info("Executing wallet pause: {0}".format(cmd))
    proc = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
    try:
        outs, errs = proc.communicate(timeout=90)
        if errs:
            app.logger.error("{0}".format(errs.decode('utf-8')))
            return False
    except TimeoutExpired as ex:
        proc.kill()
        proc.communicate()
        app.logger.info(traceback.format_exc())
        return False
    return True

def remove_connection(node_id, ip, blockchain):
    chia_binary = globals.get_blockchain_binary(blockchain)
    try:
        if blockchain in ['cactus', 'maize']:  # Cactus & Maize now supports only 'peer' command
            proc = Popen("{0} peer --remove-connection {1} full_node".format(chia_binary, node_id), stdout=PIPE, stderr=PIPE, shell=True)
        else:
            proc = Popen("{0} show --remove-connection {1}".format(chia_binary, node_id), stdout=PIPE, stderr=PIPE, shell=True)
        try:
            outs, errs = proc.communicate(timeout=30)
            if errs:
                app.logger.error(errs.decode('utf-8'))
                return False
            if outs:
                app.logger.info(outs.decode('utf-8'))
        except TimeoutExpired:
            proc.kill()
            proc.communicate()
            app.logger.error("For remove connection, the process timeout expired!")
            return False
    except Exception as ex:
        app.logger.error(traceback.format_exc())
    app.logger.info("Successfully removed connection to {0}".format(ip))
    return True

def is_plots_check_running():
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        if proc.info['name'] == 'chia' and 'plots' in proc.info['cmdline'] and 'check' in proc.info['cmdline']:
            return proc.info['pid']
    return None

def plot_check(blockchain, plot_path):
    if blockchain == 'mmx':
        app.logger.debug("MMX doesn't offer a plot check function.")
        return None
    if not os.path.exists(plot_path):
        app.logger.error("No such plot file to check at: {0}".format(plot_path))
        return None
    chia_binary = globals.get_blockchain_binary(blockchain)
    app.logger.info("Starting plot check on: {0}".format(plot_path))
    proc = Popen("{0} plots check -g {1}".format(chia_binary, plot_path),
        universal_newlines=True, stdout=PIPE, stderr=STDOUT, shell=True)
    try:
        outs, errs = proc.communicate(timeout=30)
    except TimeoutExpired:
        proc.kill()
        proc.communicate()
        raise Exception("The timeout is expired attempting to check plots.")
    app.logger.info("Completed plot check of: {0}".format(plot_path))
    class_escape = re.compile(r'.*: INFO\s+')
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return  class_escape.sub('', ansi_escape.sub('', outs))

def dispatch_action(job):
    service = job['service']
    action = job['action']
    blockchain = job['blockchain']
    app.logger.info("For blockchain:{0} Service: {1} Received action: {2}".format(blockchain, service, action))
    if service == 'networking':
        if action == "add_connections":
            conns = job['connections']
            if len(conns) == 0:
                conns.extend(websvcs.request_peers(blockchain))
            if len(conns) > 0:
                add_connections(conns, blockchain)
            else:
                app.logger.error("Received no connections from AllTheBlocks, please add directly at the command-line.")
        elif action == "remove_connection":
            remove_connection(job['node_ids'], blockchain)
    elif service == 'farming':
        if action == 'restart':
            restart_farmer(blockchain)
    elif service == 'wallet':
        if action == 'start':
            start_wallet(blockchain)
        elif action == 'pause':
            pause_wallet(blockchain)

def add_connections(connections, blockchain):
    chia_binary = globals.get_blockchain_binary(blockchain)
    for connection in connections:
        try:
            hostname,port = connection.split(':')
            if socket.gethostbyname(hostname) == hostname:
                app.logger.debug('{} is a valid IP address'.format(hostname))
            elif socket.gethostbyname(hostname) != hostname:
                app.logger.debug('{} is a valid hostname'.format(hostname))
            app.logger.info("Adding {0} connection to peer: {1}".format(blockchain, connection))
            if blockchain in ['cactus', 'maize']:  # Cactus & Maize now supports only 'peer' command
                proc = Popen("{0} peer --add-connection {1} full_node".format(chia_binary, connection), stdout=PIPE, stderr=PIPE, shell=True)
            else:
                proc = Popen("{0} show --add-connection {1}".format(chia_binary, connection), stdout=PIPE, stderr=PIPE, shell=True)
            try:
                outs, errs = proc.communicate(timeout=60)
                if errs:
                    app.logger.error(errs.decode('utf-8'))
                #app.logger.info("{0}".format(outs.decode('utf-8')))
            except TimeoutExpired:
                proc.kill()
                proc.communicate()
                app.logger.error("For add conneciton, the process timeout expired!")
        except Exception as ex:
            app.logger.error(traceback.format_exc())
            app.logger.error('Invalid connection "{0}" provided.  Must be HOST:PORT.'.format(connection))
    app.logger.info('{0} connections added to {1} and sync engaging!'.format(blockchain.capitalize(), connection))

def remove_connection(node_ids, blockchain):
    chia_binary = globals.get_blockchain_binary(blockchain)
    app.logger.debug("About to remove connection for nodeid: {0}".format(node_ids))
    for node_id in node_ids:
        try:
            proc = Popen("{0} show --remove-connection {1}".format(chia_binary, node_id), stdout=PIPE, stderr=PIPE, shell=True)
            try:
                outs, errs = proc.communicate(timeout=5)
                if errs:
                    app.logger.error(errs.decode('utf-8'))
                    app.logger.info("Error attempting to remove selected fullnode connections. See server log.")
                if outs:
                    app.logger.info(outs.decode('utf-8'))
            except TimeoutExpired:
                proc.kill()
                proc.communicate()
                app.logger.info("Timeout attempting to remove selected fullnode connections. See server log.")
        except Exception as ex:
            app.logger.info(traceback.format_exc())
    app.logger.info("Successfully removed selected connections.")

def save_wallet_settings(settings, blockchain):
    try:
        app.logger.info("Setting wallet frequency: {0}".format(settings))
        if not settings: # User reverting to defaults, no custom settings
            app.logger.info("Deleting settings at {0}".format(WALLET_SETTINGS_FILE))
            os.remove(WALLET_SETTINGS_FILE)
        else:
            app.logger.info("Updating settings at {0}".format(WALLET_SETTINGS_FILE))
            with open(WALLET_SETTINGS_FILE, 'w') as outfile:
                json.dump(settings, outfile)
    except Exception as ex:
        app.logger.debug(traceback.format_exc())
        raise Exception('Failed to store {0} wallet settings to {1}.'.format(blockchain, WALLET_SETTINGS_FILE) + '\n' + str(ex))
