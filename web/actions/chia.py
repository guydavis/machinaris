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
    farms = db.session.query(f.Farm).order_by(f.Farm.hostname).all()
    return FarmSummary(farms)

def load_plots_farming():
    plots = db.session.query(p.Plot).order_by(p.Plot.created_at.desc()).all()
    return FarmPlots(plots)

def recent_challenges():
    minute_ago = (datetime.datetime.now() - datetime.timedelta(seconds=80)).strftime("%Y-%m-%d %H:%M:%S.000")
    challenges = db.session.query(c.Challenge).filter(c.Challenge.created_at >= minute_ago).order_by(c.Challenge.created_at.desc())
    return BlockchainChallenges(challenges)

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
    worker_summary = wk.load_worker_summary()
    farmers = []
    for farmer in worker_summary.workers:
        if farmer in worker_summary.farmers:
            farmers.append({
                'hostname': farmer.hostname,
                'farming_status': farmer.farming_status().lower()
            })
        elif farmer in worker_summary.harvesters:
            farmers.append({
                'hostname': farmer.hostname,
                'farming_status': 'harvesting'
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
        utils.send_put(farmer, "/configs/farming", config, debug=False)
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
        flash('In-container path: {0}'.format(key_path), 'warning')
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
        flash('Welcome! A new key has been generated at {0} within the container filesystem. See the '.format(key_path) + \
        '<a href="https://github.com/guydavis/machinaris/wiki/Keys" target="_blank">Wiki</a> for ' + \
            'details.', 'success')
        flash('{0}'.format(" ".join(mnemonic_words)), 'info')
    if os.environ['mode'].startswith('farmer'):
        cmd = 'farmer-only'
    else:
        cmd = 'farmer'
    proc = Popen("{0} start {1}".format(CHIA_BINARY, cmd), stdout=PIPE, stderr=PIPE, shell=True)
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

def import_key(key_path, mnemonic):
    if len(mnemonic.strip().split()) != 24:
        flash('Did not receive a 24-word mnemonic seed phrase!', 'danger')
        return False
    if os.path.exists(key_path) and os.stat(key_path).st_size > 0:
        app.logger.info('Skipping key import as file exists and is NOT empty! {0}'.format(key_path))
        flash('Skipping key import as file exists and is NOT empty!', 'danger')
        flash('In container path: {0}'.format(key_path), 'warning')
        return False
    with open(key_path, 'w') as keyfile:
        keyfile.write('{0}\n'.format(mnemonic))
    time.sleep(3)
    proc = Popen("{0} keys add -f {1}".format(CHIA_BINARY, key_path), stdout=PIPE, stderr=PIPE, shell=True)
    try:
        outs, errs = proc.communicate(timeout=90)
    except TimeoutExpired:
        proc.kill()
        proc.communicate()
        app.logger.info(traceback.format_exc())
        flash('Timed out while adding key!', 'danger')
        flash(str(ex), 'warning')
        return False
    if errs:
        app.logger.info("{0}".format(errs.decode('utf-8')))
        flash('Unable to import provided mnemonic seed phrase!', 'danger')
        flash(errs.decode('utf-8'), 'warning')
        return False
    if outs:
        app.logger.debug(outs.decode('utf-8'))
    if os.environ['mode'].startswith('farmer'):
        cmd = 'farmer-only'
    else:
        cmd = 'farmer'
    proc = Popen("{0} start {1} -r".format(CHIA_BINARY, cmd), stdout=PIPE, stderr=PIPE, shell=True)
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
    if outs:
        app.logger.debug(outs.decode('utf-8'))
    flash('Welcome! Your mnemonic was imported as {0} within the container filesystem. see the '.format(key_path) + \
        '<a href="https://github.com/guydavis/machinaris/wiki/Keys" target="_blank">Wiki</a> for ' + \
            'details.', 'success')
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

def check_plots(worker, first_load):
    try:
        payload = {"service":"farming", "action":"check_plots", "first_load": first_load }
        response = utils.send_post(worker, "/analysis/", payload, debug=False)
        return response.content.decode('utf-8')
    except:
        app.logger.info(traceback.format_exc())
        flash('Failed to check plots on {0}. Please see logs.'.format(worker.hostname), 'danger')
