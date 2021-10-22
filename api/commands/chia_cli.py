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
from stat import S_ISREG, ST_CTIME, ST_MTIME, ST_MODE, ST_SIZE
from subprocess import Popen, TimeoutExpired, PIPE
from os import path

from common.config import globals
from api import app
from api.models import chia

# When reading tail of chia plots check output, limit to this many lines
MAX_LOG_LINES = 2000

def load_farm_summary(blockchain):
    chia_binary = globals.get_blockchain_binary(blockchain)
    if globals.farming_enabled() or (blockchain == 'chives' and globals.harvesting_enabled()):
        proc = Popen("{0} farm summary".format(chia_binary), stdout=PIPE, stderr=PIPE, shell=True)
        try:
            outs, errs = proc.communicate(timeout=90)
        except TimeoutExpired:
            proc.kill()
            proc.communicate()
            abort(500, description="The timeout is expired!")
        if errs:
            app.logger.debug("Error from {0} farm summary because {1}".format(blockchain, outs.decode('utf-8')))
        return chia.FarmSummary(cli_stdout=outs.decode('utf-8').splitlines())
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
    return open('/root/.{0}/mainnet/config/config.yaml'.format(blockchain),'r').read()

def save_config(config, blockchain):
    try:
        # Validate the YAML first
        yaml.safe_load(config)
        # Save a copy of the old config file
        src="/root/.{0}/mainnet/config/config.yaml".format(blockchain)
        dst="/root/.{0}/mainnet/config/config.".format(blockchain) + time.strftime("%Y%m%d-%H%M%S")+".yaml"
        shutil.copy(src,dst)
        # Now save the new contents to main config file
        with open(src, 'w') as writer:
            writer.write(config)
    except Exception as ex:
        app.logger.info(traceback.format_exc())
        raise Exception('Updated config.yaml failed validation!\n' + str(ex))
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

def load_plotnft_show(blockchain):
    chia_binary = globals.get_blockchain_binary(blockchain)
    wallet_show = ""
    child = pexpect.spawn("{0} plotnft show".format(chia_binary))
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
    proc = Popen("{0} start farmer".format(chia_binary), stdout=PIPE, stderr=PIPE, shell=True)
    try:
        outs, errs = proc.communicate(timeout=90)
    except TimeoutExpired:
        proc.kill()
        proc.communicate()
        app.logger.info(traceback.format_exc())
        flash('Timed out while starting farmer! Try restarting the Machinaris container.', 'danger')
        flash(str(ex), 'warning')
        return False
    if errs:
        app.logger.info("{0}".format(errs.decode('utf-8')))
        flash('Unable to start farmer. Try restarting the Machinaris container.'.format(key_path), 'danger')
        flash(str(ex), 'warning')
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

def check_plots(first_load):
    output_file = '/root/.chia/mainnet/log/plots_check.log'
    if not is_plots_check_running() and first_load == "true":
        try:
            log_fd = os.open(output_file, os.O_RDWR | os.O_CREAT)
            log_fo = os.fdopen(log_fd, "a+")
            proc = Popen("{0} plots check".format(CHIA_BINARY), shell=True, 
                universal_newlines=True, stdout=log_fo, stderr=log_fo)
        except:
            app.logger.info(traceback.format_exc())
            return 'Failed to start plots check job!'
        else:
            return "Starting plots check at " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    else:
        class_escape = re.compile(r' chia.plotting.(\w+)(\s+): ')
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        proc = Popen(['tail', '-n', str(MAX_LOG_LINES), output_file], stdout=PIPE)
        return  class_escape.sub('', ansi_escape.sub('', proc.stdout.read().decode("utf-8")))

def get_pool_login_link(launcher_id):
    try:
        stream = os.popen("chia plotnft get_login_link -l {0}".format(launcher_id))
        return stream.read()
    except Exception as ex:
        app.logger.info("Failed to get_login_link: {0}".format(str(ex)))
    return ""

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
