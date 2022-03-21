#
# CLI interactions with the chia binary.
#

import asyncio
import datetime
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

# When reading tail of chia plots check output, limit to this many lines
MAX_LOG_LINES = 2000

def load_farm_summary(blockchain):
    chia_binary = globals.get_blockchain_binary(blockchain)
    if globals.farming_enabled():
        proc = Popen("{0} farm summary".format(chia_binary), stdout=PIPE, stderr=PIPE, shell=True)
        try:
            outs, errs = proc.communicate(timeout=90)
        except TimeoutExpired:
            proc.kill()
            proc.communicate()
            abort(500, description="The timeout is expired!")
        if errs:
            app.logger.debug("Error from {0} farm summary because {1}".format(blockchain, outs.decode('utf-8')))
        return chia.FarmSummary(outs.decode('utf-8').splitlines(), blockchain)
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
        pass

def load_wallet_show(blockchain):
    chia_binary = globals.get_blockchain_binary(blockchain)
    wallet_show = ""
    child = pexpect.spawn("{0} wallet show".format(chia_binary))
    wallet_index = 1
    while True:
        i = child.expect(["Wallet height:.*\r\n", "Choose wallet key:.*\r\n", "No online backup file found.*\r\n"], timeout=120)
        if i == 0:
            app.logger.debug("wallet show returned 'Wallet height...' so collecting details.")
            wallet_show += child.after.decode("utf-8") + child.before.decode("utf-8") + child.read().decode("utf-8")
            break
        elif i == 1:
            app.logger.debug("wallet show got index prompt so selecting #{0}".format(wallet_index))
            child.sendline("{0}".format(wallet_index))
            wallet_index += 1
        elif i == 2:
            child.sendline("S")
        else:
            app.logger.debug("pexpect returned {0}".format(i))
            wallet_show += "ERROR:\n" + child.after.decode("utf-8") + child.before.decode("utf-8") + child.read().decode("utf-8")
    return chia.Wallet(wallet_show)

def load_blockchain_show(blockchain):
    chia_binary = globals.get_blockchain_binary(blockchain)
    proc = Popen("{0} show --state".format(chia_binary), stdout=PIPE, stderr=PIPE, shell=True)
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
    chia_binary = globals.get_blockchain_binary(blockchain)
    proc = Popen("{0} show --connections".format(chia_binary), stdout=PIPE, stderr=PIPE, shell=True)
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
    chia_binary = globals.get_blockchain_binary(blockchain)
    proc = Popen("{0} keys show".format(chia_binary), stdout=PIPE, stderr=PIPE, shell=True)
    try:
        outs, errs = proc.communicate(timeout=90)
    except TimeoutExpired:
        proc.kill()
        proc.communicate()
        abort(500, description="The timeout is expired!")
    if errs:
        abort(500, description=errs.decode('utf-8'))
    return chia.Keys(outs.decode('utf-8').splitlines())

def start_farmer(blockchain):
    chia_binary = globals.get_blockchain_binary(blockchain)
    proc = Popen("{0} start farmer -r".format(chia_binary), stdout=PIPE, stderr=PIPE, shell=True)
    try:
        outs, errs = proc.communicate(timeout=90)
    except TimeoutExpired as ex:
        proc.kill()
        proc.communicate()
        app.logger.info(traceback.format_exc())
        return False
    if errs:
        app.logger.info("{0}".format(errs.decode('utf-8')))
        return False
    return True

def remove_connection(node_id, ip, blockchain):
    chia_binary = globals.get_blockchain_binary(blockchain)
    try:
        proc = Popen("{0} show --remove-connection {1}".format(chia_binary, node_id), stdout=PIPE, stderr=PIPE, shell=True)
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
    proc = Popen("{0} plots check -g {1}".format(chia_binary, plot_path),
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

def dispatch_action(job):
    service = job['service']
    action = job['action']
    blockchain = job['blockchain']
    if service == 'networking':
        if action == "add_connection":
            add_connection(job['connection'], blockchain)
        elif action == "remove_connection":
            remove_connection(job['node_ids'], blockchain)

def add_connection(connection, blockchain):
    chia_binary = globals.get_blockchain_binary(blockchain)
    try:
        hostname,port = connection.split(':')
        if socket.gethostbyname(hostname) == hostname:
            app.logger.debug('{} is a valid IP address'.format(hostname))
        elif socket.gethostbyname(hostname) != hostname:
            app.logger.debug('{} is a valid hostname'.format(hostname))
        proc = Popen("{0} show --add-connection {1}".format(chia_binary, connection), stdout=PIPE, stderr=PIPE, shell=True)
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

def remove_connection(node_ids, blockchain):
    chia_binary = globals.get_blockchain_binary(blockchain)
    app.logger.debug("About to remove connection for nodeid: {0}".format(node_ids))
    for node_id in node_ids:
        try:
            proc = Popen("{0} show --remove-connection {1}".format(chia_binary, node_id), stdout=PIPE, stderr=PIPE, shell=True)
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
