#
# CLI interactions with the chia binary.
#

import datetime
import os
import shutil
import socket
import time
import traceback
import yaml

from flask import Flask, jsonify, abort, request, flash
from stat import S_ISREG, ST_CTIME, ST_MODE, ST_SIZE
from subprocess import Popen, TimeoutExpired, PIPE
from os import path

from app import app
from app.models import chia
from app.commands import global_config

CHIA_BINARY = '/chia-blockchain/venv/bin/chia'

RELOAD_MINIMUM_SECS = 30 # Don't query chia unless at least this long since last time.

last_farm_summary = None 
last_farm_summary_load_time = None 

def load_farm_summary():
    global last_farm_summary
    global last_farm_summary_load_time
    if last_farm_summary and last_farm_summary_load_time >= \
            (datetime.datetime.now() - datetime.timedelta(seconds=RELOAD_MINIMUM_SECS)):
        return last_farm_summary

    if global_config.plotting_only():  # Just get plot count and size
        last_farm_summary = chia.FarmSummary(farm_plots=load_plots_farming())
    else: # Load from chia farm summary
        proc = Popen("{0} farm summary".format(CHIA_BINARY), stdout=PIPE, stderr=PIPE, shell=True)
        try:
            outs, errs = proc.communicate(timeout=90)
        except TimeoutExpired:
            proc.kill()
            proc.communicate()
            abort(500, description="The timeout is expired!")
        if errs:
            abort(500, description=errs.decode('utf-8'))
        last_farm_summary = chia.FarmSummary(cli_stdout=outs.decode('utf-8').splitlines())
    last_farm_summary_load_time = datetime.datetime.now()
    return last_farm_summary

last_plots_farming = None 
last_plots_farming_load_time = None 

def load_plots_farming():
    global last_plots_farming
    global last_plots_farming_load_time
    if last_plots_farming and last_plots_farming_load_time >= \
            (datetime.datetime.now() - datetime.timedelta(seconds=RELOAD_MINIMUM_SECS)):
        return last_plots_farming
    dir_path = '/plots' # TODO Pull list from 'chia plots show'
    entries = (os.path.join(dir_path, file_name) for file_name in os.listdir(dir_path))
    entries = ((os.stat(path), path) for path in entries)
    entries = ((stat[ST_CTIME], stat[ST_SIZE], path) for stat, path in entries if S_ISREG(stat[ST_MODE]))
    last_plots_farming = chia.FarmPlots(entries)
    last_plots_farming_load_time = datetime.datetime.now()
    return last_plots_farming

def save_config(config):
    try:
        # Validate the YAML first
        yaml.safe_load(config)
        # Save a copy of the old config file
        src="/root/.chia/mainnet/config/config.yaml"
        dst="/root/.chia/mainnet/config/config."+time.strftime("%Y%m%d-%H%M%S")+".yaml"
        shutil.copy(src,dst)
        # Now save the new contents to main config file
        with open(src, 'w') as writer:
            writer.write(config)
    except Exception as ex:
        traceback.print_exc()
        flash('Updated config.yaml failed validation! Fix and save or refresh page.', 'danger')
        flash(str(ex), 'warning')
    else:
        flash('Nice! config.yaml validated and saved successfully.', 'success')
        flash('NOTE: Currently requires restarting the container to pickup changes.', 'info')

last_wallet_show = None 
last_wallet_show_load_time = None 

def load_wallet_show():
    global last_wallet_show
    global last_wallet_show_load_time
    if last_wallet_show and last_wallet_show_load_time >= \
            (datetime.datetime.now() - datetime.timedelta(seconds=RELOAD_MINIMUM_SECS)):
        return last_wallet_show

    proc = Popen("{0} wallet show".format(CHIA_BINARY), stdout=PIPE, stderr=PIPE, shell=True)
    try:
        outs, errs = proc.communicate(timeout=90)
    except TimeoutExpired:
        proc.kill()
        proc.communicate()
        abort(500, description="The timeout is expired!")
    if errs:
        abort(500, description=errs.decode('utf-8'))
    
    last_wallet_show = chia.Keys(outs.decode('utf-8').splitlines())
    last_wallet_show_load_time = datetime.datetime.now()
    return last_wallet_show

last_blockchain_show = None 
last_blockchain_show_load_time = None 

def load_blockchain_show():
    global last_blockchain_show
    global last_blockchain_show_load_time
    if last_blockchain_show and last_blockchain_show_load_time >= \
            (datetime.datetime.now() - datetime.timedelta(seconds=RELOAD_MINIMUM_SECS)):
        return last_blockchain_show

    proc = Popen("{0} show --state".format(CHIA_BINARY), stdout=PIPE, stderr=PIPE, shell=True)
    try:
        outs, errs = proc.communicate(timeout=90)
    except TimeoutExpired:
        proc.kill()
        proc.communicate()
        abort(500, description="The timeout is expired!")
    if errs:
        abort(500, description=errs.decode('utf-8'))
    
    last_blockchain_show = chia.Blockchain(outs.decode('utf-8').splitlines())
    last_blockchain_show_load_time = datetime.datetime.now()
    return last_blockchain_show

last_connections_show = None 
last_connections_show_load_time = None 

def load_connections_show():
    global last_connections_show
    global last_connections_show_load_time
    if last_connections_show and last_connections_show_load_time >= \
            (datetime.datetime.now() - datetime.timedelta(seconds=RELOAD_MINIMUM_SECS)):
        return last_connections_show

    proc = Popen("{0} show --connections".format(CHIA_BINARY), stdout=PIPE, stderr=PIPE, shell=True)
    try:
        outs, errs = proc.communicate(timeout=90)
    except TimeoutExpired:
        proc.kill()
        proc.communicate()
        abort(500, description="The timeout is expired!")
    if errs:
        abort(500, description=errs.decode('utf-8'))
    
    last_connections_show = chia.Connections(outs.decode('utf-8').splitlines())
    last_connections_show_load_time = datetime.datetime.now()
    return last_connections_show

def add_connection(connection):
    try:
        hostname,port = connection.split(':')
        if socket.gethostbyname(hostname) == hostname:
            app.logger.info('{} is a valid IP address'.format(hostname))
        elif socket.gethostbyname(hostname) != hostname:
            app.logger.info('{} is a valid hostname'.format(hostname))
        proc = Popen("{0} show --add-connection {1}".format(CHIA_BINARY, connection), stdout=PIPE, stderr=PIPE, shell=True)
        try:
            outs, errs = proc.communicate(timeout=60)
        except TimeoutExpired:
            proc.kill()
            proc.communicate()
            abort(500, description="The timeout is expired!")
        if errs:
            abort(500, description=errs.decode('utf-8'))
    except Exception as ex:
        app.logger.info(traceback.format_exc())
        flash('Invalid connection "{0}" provided.  Must be HOST:PORT.'.format(connection), 'danger')
        flash(str(ex), 'warning')
    else:
        app.logger.info("{0}".format(outs.decode('utf-8')))
        flash('Nice! Connection added to Chia and sync engaging!', 'success')

last_keys_show = None 
last_keys_show_load_time = None 

def load_keys_show():
    global last_keys_show
    global last_keys_show_load_time
    if last_keys_show and last_keys_show_load_time >= \
            (datetime.datetime.now() - datetime.timedelta(seconds=RELOAD_MINIMUM_SECS)):
        return last_keys_show

    proc = Popen("{0} keys show".format(CHIA_BINARY), stdout=PIPE, stderr=PIPE, shell=True)
    try:
        outs, errs = proc.communicate(timeout=90)
    except TimeoutExpired:
        proc.kill()
        proc.communicate()
        abort(500, description="The timeout is expired!")
    if errs:
        abort(500, description=errs.decode('utf-8'))
    
    last_keys_show = chia.Wallet(outs.decode('utf-8').splitlines())
    last_keys_show_load_time = datetime.datetime.now()
    return last_keys_show 