#
# CLI interactions with the chia binary.
#

import datetime
import os
import shutil
import time
import traceback
import yaml

from flask import Flask, jsonify, abort, request, flash
from stat import S_ISREG, ST_CTIME, ST_MODE
from subprocess import Popen, TimeoutExpired, PIPE
from os import path

from app.models import chia

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

    proc = Popen("{0} farm summary".format(CHIA_BINARY), stdout=PIPE, stderr=PIPE, shell=True)
    try:
        outs, errs = proc.communicate(timeout=90)
    except TimeoutExpired:
        proc.kill()
        proc.communicate()
        abort(500, description="The timeout is expired!")
    if errs:
        abort(500, description=errs.decode('utf-8'))
    
    last_farm_summary = chia.FarmSummary(outs.decode('utf-8').splitlines())
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
    entries = ((stat[ST_CTIME], path) for stat, path in entries if S_ISREG(stat[ST_MODE]))
    last_plots_farming = chia.FarmPlots(entries)
    last_plots_farming_load_time = datetime.datetime.now()
    return last_plots_farming

def is_setup():
    # If farming, then need 'keys' variable set to a mnemonic.txt file or similar
    # See https://github.com/Chia-Network/chia-docker/blob/main/entrypoint.sh#L7
    return "keys" in os.environ and path.exists(os.environ['keys'])

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
    
    last_wallet_show = chia.Wallet(outs.decode('utf-8').splitlines())
    last_wallet_show_load_time = datetime.datetime.now()
    return last_wallet_show