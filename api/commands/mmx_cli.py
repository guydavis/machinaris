#
# CLI interactions with the mmx binary.
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

from flask import Flask, jsonify, abort, request, flash
from stat import S_ISREG, ST_CTIME, ST_MTIME, ST_MODE, ST_SIZE
from subprocess import Popen, TimeoutExpired, PIPE, STDOUT
from os import path

from common.config import globals
from api import app
from api.models import chia

def load_farm_info(blockchain):
    mmx_binary = globals.get_blockchain_binary(blockchain)
    if globals.farming_enabled():
        lines = []
        proc = Popen("{0} farm info".format(mmx_binary), stdout=PIPE, stderr=PIPE, shell=True)
        try:
            outs, errs = proc.communicate(timeout=90)
        except TimeoutExpired:
            proc.kill()
            proc.communicate()
            abort(500, description="The timeout is expired!")
        if errs:
            app.logger.debug("Error from {0} farm summary because {1}".format(blockchain, outs.decode('utf-8')))
        lines.extend(outs.decode('utf-8').splitlines())
        proc = Popen("{0} farm info".format(mmx_binary), stdout=PIPE, stderr=PIPE, shell=True)
        try:
            outs, errs = proc.communicate(timeout=90)
        except TimeoutExpired:
            proc.kill()
            proc.communicate()
            abort(500, description="The timeout is expired!")
        if errs:
            app.logger.debug("Error from {0} farm summary because {1}".format(blockchain, outs.decode('utf-8')))
        lines.extend(outs.decode('utf-8').splitlines())
        return chia.FarmSummary(lines, blockchain)
    elif globals.harvesting_enabled():
        return chia.HarvesterSummary()
    else:
        raise Exception("Unable to load farm summary on non-farmer and non-harvester.")

def load_plots_farming():
    all_entries = []
    for dir_path in os.environ['plots_dir'].split(':'):
        try:
            entries = (os.path.join(dir_path, file_name) for file_name in os.listdir(dir_path))
            entries = ((os.stat(path), path) for path in entries)
            entries = ((stat[ST_MTIME], stat[ST_SIZE], path) for stat, path in entries if S_ISREG(stat[ST_MODE]))
            all_entries.extend(entries)
        except:
            app.logger.info("Failed to list files at {0}".format(dir_path))
            app.logger.info(traceback.format_exc())
    all_entries = sorted(all_entries, key=lambda entry: entry[0], reverse=True)
    plots_farming = chia.FarmPlots(all_entries)
    return plots_farming

def load_config(blockchain):
    mainnet = globals.get_blockchain_network_path(blockchain)
    return open(f'{mainnet}/config/Node.json','r').read()

def save_config(config, blockchain):
    try:
        mainnet = globals.get_blockchain_network_path(blockchain)
        # Validate the json first
        json.load(config)
        # Save a copy of the old config file
        src=f'{mainnet}/config/Node.json'
        dst=f'{mainnet}/config/Node.json' + time.strftime("%Y%m%d-%H%M%S")+".yaml"
        shutil.copy(src,dst)
        # Now save the new contents to main config file
        with open(src, 'w') as writer:
            writer.write(config)
    except Exception as ex:
        app.logger.info(traceback.format_exc())
        raise Exception('Updated Node.json failed validation!\n' + str(ex))
    else:
        pass

def load_wallet_show(blockchain):
    mmx_binary = globals.get_blockchain_binary(blockchain)
    proc = Popen("{0} wallet show".format(mmx_binary), stdout=PIPE, stderr=PIPE, shell=True)
    try:
        outs, errs = proc.communicate(timeout=90)
    except TimeoutExpired:
        proc.kill()
        proc.communicate()
        abort(500, description="The timeout is expired!")
    if errs:
        abort(500, description=errs.decode('utf-8'))
    return chia.Wallet(outs.decode('utf-8'))

def load_blockchain_show(blockchain):
    mmx_binary = globals.get_blockchain_binary(blockchain)
    proc = Popen("{0} node info".format(mmx_binary), stdout=PIPE, stderr=PIPE, shell=True)
    try:
        outs, errs = proc.communicate(timeout=90)
    except TimeoutExpired:
        proc.kill()
        proc.communicate()
        abort(500, description="The timeout is expired!")
    if errs:
        abort(500, description=errs.decode('utf-8'))
    return chia.Blockchain(outs.decode('utf-8').splitlines())

def load_connections_show(blockchain):
    mmx_binary = globals.get_blockchain_binary(blockchain)
    proc = Popen("{0} node peers".format(mmx_binary), stdout=PIPE, stderr=PIPE, shell=True)
    try:
        outs, errs = proc.communicate(timeout=90)
    except TimeoutExpired:
        proc.kill()
        proc.communicate()
        abort(500, description="The timeout is expired!")
    if errs:
        abort(500, description=errs.decode('utf-8'))
    return chia.Connections(outs.decode('utf-8').splitlines())

def load_keys_show(blockchain):
    mmx_binary = globals.get_blockchain_binary(blockchain)
    proc = Popen("{0} wallet keys".format(mmx_binary), stdout=PIPE, stderr=PIPE, shell=True)
    try:
        outs, errs = proc.communicate(timeout=90)
    except TimeoutExpired:
        proc.kill()
        proc.communicate()
        abort(500, description="The timeout is expired!")
    if errs:
        abort(500, description=errs.decode('utf-8'))
    return chia.Keys(outs.decode('utf-8').splitlines())

# TODO 
def start_farmer(blockchain):
    mmx_binary = globals.get_blockchain_binary(blockchain)
    proc = Popen("{0} start farmer -r".format(mmx_binary), stdout=PIPE, stderr=PIPE, shell=True)
    try:
        outs, errs = proc.communicate(timeout=90)
    except TimeoutExpired as ex:
        proc.kill()
        proc.communicate()
        app.logger.info(traceback.format_exc())
        flash('Timed out while starting farmer! Try restarting the Machinaris container.', 'danger')
        flash(str(ex), 'warning')
        return False
    if errs:
        app.logger.info("{0}".format(errs.decode('utf-8')))
        flash('Unable to start farmer. Try restarting the Machinaris container instead.', 'danger')
        return False
    return True

# TODO
def remove_connection(node_id, ip, blockchain):
    mmx_binary = globals.get_blockchain_binary(blockchain)
    try:
        proc = Popen("{0} show --remove-connection {1}".format(mmx_binary, node_id), stdout=PIPE, stderr=PIPE, shell=True)
        try:
            outs, errs = proc.communicate(timeout=90)
        except TimeoutExpired:
            proc.kill()
            proc.communicate()
            app.logger.info("The timeout is expired!")
            return False
        if errs:
            app.logger.info(errs.decode('utf-8'))
            return False
        if outs:
            app.logger.info(outs.decode('utf-8'))
    except Exception as ex:
        app.logger.info(traceback.format_exc())
    app.logger.info("Successfully removed connection to {0}".format(ip))
    return True

# TODO
def is_plots_check_running():
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        if proc.info['name'] == 'chia' and 'plots' in proc.info['cmdline'] and 'check' in proc.info['cmdline']:
            return proc.info['pid']
    return None
# TODO
def plot_check(blockchain, plot_path):
    if not os.path.exists(plot_path):
        app.logger.error("No such plot file to check at: {0}".format(plot_path))
        return None
    mmx_binary = globals.get_blockchain_binary(blockchain)
    proc = Popen("{0} plots check -g {1}".format(mmx_binary, plot_path),
        universal_newlines=True, stdout=PIPE, stderr=STDOUT, shell=True)
    try:
        outs, errs = proc.communicate(timeout=90)
    except TimeoutExpired:
        proc.kill()
        proc.communicate()
        abort(500, description="The timeout is expired attempting to check plots.")
    class_escape = re.compile(r'.*: INFO\s+')
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return  class_escape.sub('', ansi_escape.sub('', outs))

# TODO
def dispatch_action(job):
    service = job['service']
    action = job['action']
    blockchain = job['blockchain']
    if service == 'networking':
        if action == "add_connection":
            add_connection(job['connection'], blockchain)
        elif action == "remove_connection":
            remove_connection(job['node_ids'], blockchain)

# TODO
def add_connection(connection, blockchain):
    mmx_binary = globals.get_blockchain_binary(blockchain)
    try:
        hostname,port = connection.split(':')
        if socket.gethostbyname(hostname) == hostname:
            app.logger.debug('{} is a valid IP address'.format(hostname))
        elif socket.gethostbyname(hostname) != hostname:
            app.logger.debug('{} is a valid hostname'.format(hostname))
        proc = Popen("{0} show --add-connection {1}".format(mmx_binary, connection), stdout=PIPE, stderr=PIPE, shell=True)
        try:
            outs, errs = proc.communicate(timeout=90)
        except TimeoutExpired:
            proc.kill()
            proc.communicate()
            abort(500, description="The timeout is expired!")
        if errs:
            abort(500, description=errs.decode('utf-8'))
    except Exception as ex:
        app.logger.info(traceback.format_exc())
        app.logger.info('Invalid connection "{0}" provided.  Must be HOST:PORT.'.format(connection))
    else:
        app.logger.info("{0}".format(outs.decode('utf-8')))
        app.logger.info('{0} connection added to {1} and sync engaging!'.format(blockchain.capitalize(), connection))

# TODO
def remove_connection(node_ids, blockchain):
    mmx_binary = globals.get_blockchain_binary(blockchain)
    app.logger.debug("About to remove connection for nodeid: {0}".format(node_ids))
    for node_id in node_ids:
        try:
            proc = Popen("{0} show --remove-connection {1}".format(mmx_binary, node_id), stdout=PIPE, stderr=PIPE, shell=True)
            try:
                outs, errs = proc.communicate(timeout=5)
            except TimeoutExpired:
                proc.kill()
                proc.communicate()
                app.logger.info("Timeout attempting to remove selected fullnode connections. See server log.")
            if errs:
                app.logger.error(errs.decode('utf-8'))
                app.logger.info("Error attempting to remove selected fullnode connections. See server log.")
            if outs:
                app.logger.debug(outs.decode('utf-8'))
        except Exception as ex:
            app.logger.info(traceback.format_exc())
    app.logger.info("Successfully removed selected connections.")
