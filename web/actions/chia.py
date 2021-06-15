#
# CLI interactions with the chia binary.
#

import datetime
import os
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

from web import app, db, utils
from common.models import farms as f, plots as p, challenges as c, wallets as w, \
    blockchains as b, connections as co, keys as k
from common.config import globals
from web.models.chia import FarmSummary, FarmPlots, BlockchainChallenges, Wallets, \
    Blockchains, Connections, Keys
from . import worker as wk

CHIA_BINARY = '/chia-blockchain/venv/bin/chia'

def load_farm_summary():
    farms = db.session.query(f.Farm).all()
    return FarmSummary(farms)

def load_plots_farming():
    plots = db.session.query(p.Plot).all()
    return FarmPlots(plots)

def recent_challenges():
    minute_ago = (datetime.datetime.now() - datetime.timedelta(minutes=2)).strftime("%Y-%m-%d %H:%M:%S.000")
    challenges = db.session.query(c.Challenge).filter(c.Challenge.created_at >= minute_ago).order_by(c.Challenge.created_at.desc())
    return BlockchainChallenges(challenges[:8]) # Last minute challenge

def load_wallets():
    wallets = db.session.query(w.Wallet).all()
    return Wallets(wallets)

def load_blockchain_show():
    blockchains = db.session.query(b.Blockchain).all()
    return Blockchains(blockchains)

def load_connections_show():
    connections = db.session.query(co.Connection).all()
    return Connections(connections)

def load_keys_show():
    keys = db.session.query(k.Key).all()
    return Keys(keys)

def load_farmers():
    farmers = []
    for farmer in wk.load_worker_summary().farmers:
        farmers.append({
            'hostname': farmer.hostname,
            'farming_status': farmer.farming_status().lower()
        })
    return farmers

def load_config(farmer):
    return utils.send_get(farmer, "/configs/farming", debug=False).content

def save_config(farmer, config):
    try: # Validate the YAML first
        yaml.safe_load(config)
    except Exception as ex:
        app.logger.info(traceback.format_exc())
        flash('Updated config.yaml failed validation! Fix and save or refresh page.', 'danger')
        flash(str(ex), 'warning')
    try:
        utils.send_put(farmer, "/configs/farming", config, debug=True)
    except Exception as ex:
        flash('Failed to save config to farmer.  Please check log files.', 'danger')
        flash(str(ex), 'warning')
    else:
        flash('Nice! Chia\'s config.yaml validated and saved successfully.', 'success')

def add_connection(connection):
    try:
        hostname,port = connection.split(':')
        if socket.gethostbyname(hostname) == hostname:
            app.logger.info('{} is a valid IP address'.format(hostname))
        elif socket.gethostbyname(hostname) != hostname:
            app.logger.info('{} is a valid hostname'.format(hostname))
        proc = Popen("{0} show --add-connection {1}".format(CHIA_BINARY, connection), stdout=PIPE, stderr=PIPE, shell=True)
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
        flash('Invalid connection "{0}" provided.  Must be HOST:PORT.'.format(connection), 'danger')
        flash(str(ex), 'warning')
    else:
        app.logger.info("{0}".format(outs.decode('utf-8')))
        flash('Nice! Connection added to Chia and sync engaging!', 'success')

def generate_key(key_path):
    if os.path.exists(key_path) and os.stat(key_path).st_size > 0:
        app.logger.info('Skipping key generation as file exists and is NOT empty! {0}'.format(key_path))
        flash('Skipping key generation as file exists and is NOT empty!', 'danger')
        flash('key_path={0}'.format(key_path), 'warning')
        return False
    proc = Popen("{0} keys generate".format(CHIA_BINARY), stdout=PIPE, stderr=PIPE, shell=True)
    try:
        outs, errs = proc.communicate(timeout=90)
    except TimeoutExpired:
        proc.kill()
        proc.communicate()
        app.logger.info(traceback.format_exc())
        flash('Timed out while generating keys!', 'danger')
        flash(str(ex), 'warning')
        return False
    if errs:
        app.logger.info("{0}".format(errs.decode('utf-8')))
        flash('Unable to generate keys!', 'danger')
        return False
    proc = Popen("{0} keys show --show-mnemonic-seed | tail -n 1 > {1}".format(CHIA_BINARY, key_path), stdout=PIPE, stderr=PIPE, shell=True)
    try:
        outs, errs = proc.communicate(timeout=90)
    except TimeoutExpired:
        proc.kill()
        proc.communicate()
        app.logger.info(traceback.format_exc())
        flash('Timed out while generating keys!', 'danger')
        flash(str(ex), 'warning')
        return False
    if errs:
        app.logger.info("{0}".format(errs.decode('utf-8')))
        flash('Unable to save mnemonic to {0}'.format(key_path), 'danger')
        return False
    else:
        app.logger.info("Store mnemonic output: {0}".format(outs.decode('utf-8')))
        try:
            mnemonic_words = open(key_path,'r').read().split()
            if len(mnemonic_words) != 24:
                flash('{0} does not contain a 24-word mnemonic!'.format(key_path), 'danger')
                return False
        except:
                flash('{0} was unreadable or not found.'.format(key_path), 'danger')
                return False
        flash('Welcome! A new key has been generated at {0}. Keep it secret! Keep it safe!'.format(key_path), 'success')
        flash('{0}'.format(" ".join(mnemonic_words)), 'info')
    proc = Popen("{0} start farmer".format(CHIA_BINARY), stdout=PIPE, stderr=PIPE, shell=True)
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

def remove_connection(node_id, ip):
    try:
        proc = Popen("{0} show --remove-connection {1}".format(CHIA_BINARY, node_id), stdout=PIPE, stderr=PIPE, shell=True)
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

def compare_plot_counts(global_config, farming, plots):
    if farming:
        try:
            if int(farming.plot_count) < len(plots.rows):
                flash("Warning! Chia is farming {0} plots, but Machinaris found {1} *.plot files on disk. See the <a href='https://github.com/guydavis/machinaris/wiki/FAQ#warning-chia-is-farming-x-plots-but-machinaris-found-y-plot-files-on-disk' target='_blank'>FAQ</a>.".format(farming.plot_count, len(plots.rows), 'warning'))
        except:
            app.logger.info("Compare plots failed to check matching plot counts.")
            app.logger.info(traceback.format_exc())

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
            return "Starting chia plots check at " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    else:
        class_escape = re.compile(r' chia.plotting.(\w+)(\s+): ')
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        proc = Popen(['tail', '-n', str(MAX_LOG_LINES), output_file], stdout=PIPE)
        return  class_escape.sub('', ansi_escape.sub('', proc.stdout.read().decode("utf-8")))
