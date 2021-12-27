#
# CLI interactions with the chia binary.
#

import datetime
import json
import os
import pexpect
import psutil
import re
import requests
import signal
import shutil
import socket
import sys
import time
import traceback
import urllib
import yaml

from flask import Flask, jsonify, abort, request, flash, url_for
from flask.helpers import make_response
from stat import S_ISREG, ST_CTIME, ST_MTIME, ST_MODE, ST_SIZE
from subprocess import Popen, TimeoutExpired, PIPE
from sqlalchemy import or_
from os import path

from web import app, db, utils
from common.models import farms as f, plots as p, challenges as c, wallets as w, \
    blockchains as b, connections as co, keys as k
from common.config import globals
from web.models.chia import FarmSummary, FarmPlots, Wallets, \
    Blockchains, Connections, Keys, ChallengesChartData
from . import worker as wk

COLD_WALLET_ADDRESSES_FILE = '/root/.chia/machinaris/config/cold_wallet_addresses.json'

def load_farm_summary():
    farms = db.session.query(f.Farm).order_by(f.Farm.hostname).all()
    wallets = db.session.query(w.Wallet).order_by(w.Wallet.blockchain).all()
    if len(farms) == 0:
        flash("Relax and grab a coffee. Status is being gathered from active workers.  Please allow 15 minutes...", 'info')
    return FarmSummary(farms, wallets)

def load_plots_farming(hostname=None):
    return FarmPlots([])  # Only used for columns on Farming table, no data

def order_plots_query(args, query):
    column = None
    col_idx = int(request.args.get("order[0][column]"))
    if col_idx == 0:
        column = p.Plot.displayname
    elif col_idx == 1:
        column = p.Plot.blockchain
    elif col_idx == 2:
        column = p.Plot.plot_id
    elif col_idx == 3:
        column = p.Plot.dir
    elif col_idx == 4:
        column = p.Plot.file
    elif col_idx == 5:
        column = p.Plot.type
    elif col_idx == 6:
        column = p.Plot.created_at
    elif col_idx == 7:
        column = p.Plot.size
    elif col_idx == 8:
        column = p.Plot.plot_check
    if request.args.get("order[0][dir]") == "desc":
        query = query.order_by(column.desc())
    else:
        query = query.order_by(column.asc())
    return query

def search_plots_query(search, query):
    app.logger.info("Searching all plots for: {0}".format(search))
    query = query.filter(or_(
        p.Plot.displayname.like(search),
        p.Plot.blockchain.like(search),
        p.Plot.plot_id.like(search),
        p.Plot.dir.like(search),
        p.Plot.file.like(search),
        p.Plot.type.like(search),
        p.Plot.created_at.like(search),
        p.Plot.plot_check.like(search),
    ))
    return query

def load_plots(args):
    total_count = db.session.query(p.Plot).count()
    filtered_count = total_count
    query = db.session.query(p.Plot)
    draw = int(request.args.get("draw"))  # Request identifier from Datatables.js
    #columns = request.args.getlist("columns")  # Indexed list like column[0][...]
    query = order_plots_query(args, query)
    search = request.args.get("search[value]")
    if search:
        query = search_plots_query(search, query)
        filtered_count = query.count()
    start = int(request.args.get("start"))
    if start > 0:
        query = query.offset(start)
    length = int(request.args["length"])
    if length > 0: 
        query = query.limit(length)
    return [draw, total_count, filtered_count, FarmPlots(query).rows]

def challenges_chart_data(farm_summary):
    chart_start_time = (datetime.datetime.now() - datetime.timedelta(minutes=app.config['MAX_CHART_CHALLENGES_MINS'])).strftime("%Y-%m-%d %H:%M:%S.000")
    for blockchain in farm_summary.farms:
        challenges = db.session.query(c.Challenge).filter(c.Challenge.blockchain==blockchain,
            c.Challenge.created_at >= chart_start_time).order_by(
            c.Challenge.created_at.desc(), c.Challenge.hostname).all()
        farm_summary.farms[blockchain]['challenges'] = ChallengesChartData(challenges)

def load_wallets():
    wallets = db.session.query(w.Wallet).order_by(w.Wallet.blockchain).all()
    cold_wallet_addresses = load_cold_wallet_addresses()
    return Wallets(wallets, cold_wallet_addresses)

def load_blockchain_show():
    try:  
        blockchains = db.session.query(b.Blockchain).order_by(b.Blockchain.blockchain).all()
        return Blockchains(blockchains)
    except Exception as ex:
        app.logger.error("Error querying for blockchains: {0}".format(str(ex)))
    return None

def load_connections_show():
    connections = db.session.query(co.Connection).all()
    return Connections(connections)

def load_keys_show():
    keys = db.session.query(k.Key).order_by(k.Key.blockchain).all()
    return Keys(keys)
    
def load_farmers():
    return wk.load_worker_summary().farmers_harvesters()

def load_config(farmer, blockchain):
    return utils.send_get(farmer, "/configs/farming/"+ blockchain, debug=False).content

def save_config(farmer, blockchain, config):
    try: # Validate the YAML first
        yaml.safe_load(config)
    except Exception as ex:
        app.logger.info(traceback.format_exc())
        flash('Updated config.yaml failed validation! Fix and save or refresh page.', 'danger')
        flash(str(ex), 'warning')
    try:
        utils.send_put(farmer, "/configs/farming/" + blockchain, config, debug=False)
    except Exception as ex:
        flash('Failed to save config to farmer.  Please check log files.', 'danger')
        flash(str(ex), 'warning')
    else:
        flash('Nice! Chia\'s config.yaml validated and saved successfully. Please restart the Machinaris worker to take effect.', 'success')

def generate_key(key_path, blockchain):
    chia_binary = globals.get_blockchain_binary(blockchain)
    if os.path.exists(key_path) and os.stat(key_path).st_size > 0:
        app.logger.info('Skipping key generation as file exists and is NOT empty! {0}'.format(key_path))
        flash('Skipping key generation as file exists and is NOT empty!', 'danger')
        flash('In-container path: {0}'.format(key_path), 'warning')
        return False
    proc = Popen("{0} keys generate".format(chia_binary), stdout=PIPE, stderr=PIPE, shell=True)
    try:
        outs, errs = proc.communicate(timeout=90)
    except TimeoutExpired as ex:
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
    proc = Popen("{0} keys show --show-mnemonic-seed | tail -n 1 > {1}".format(chia_binary, key_path), stdout=PIPE, stderr=PIPE, shell=True)
    try:
        outs, errs = proc.communicate(timeout=90)
    except TimeoutExpired as ex:
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
        flash('Welcome! A new key has been generated, see below. Please visit the ' + \
        '<a href="https://github.com/guydavis/machinaris/wiki#basic-configuration" target="_blank">Wiki</a> to get started with Machinaris. ' \
        'Please allow 5-10 minutes for Chia to begin syncing with peers...', 'success')
        flash('{0}'.format(" ".join(mnemonic_words)), 'info')
    if os.environ['mode'].startswith('farmer'):
        cmd = 'farmer-only'
    else:
        cmd = 'farmer'
    proc = Popen("{0} start {1}".format(chia_binary, cmd), stdout=PIPE, stderr=PIPE, shell=True)
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
        flash('Unable to start farmer. Try restarting the Machinaris container.'.format(key_path), 'danger')
        return False
    return True

def import_key(key_path, mnemonic, blockchain):
    chia_binary = globals.get_blockchain_binary(blockchain)
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
    proc = Popen("{0} keys add -f {1}".format(chia_binary, key_path), stdout=PIPE, stderr=PIPE, shell=True)
    try:
        outs, errs = proc.communicate(timeout=90)
    except TimeoutExpired as ex:
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
    proc = Popen("{0} start {1} -r".format(chia_binary, cmd), stdout=PIPE, stderr=PIPE, shell=True)
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
        flash('Unable to start farmer. Try restarting the Machinaris container.'.format(key_path), 'danger')
        return False
    if outs:
        app.logger.debug(outs.decode('utf-8'))
    flash('Welcome! Your mnemonic key was imported. See the ' + \
        '<a href="https://github.com/guydavis/machinaris/wiki#basic-configuration" target="_blank">Wiki</a> to get started with Machinaris. ' \
        'Please allow 5-10 minutes for Chia to begin syncing with peers...', 'success')
    return True

def add_connection(connection, hostname, blockchain):
    try:
        host,port = connection.split(':')
        if socket.gethostbyname(host) == host:
            app.logger.info('{} is a valid IP address'.format(host))
        elif socket.gethostbyname(host) != host:
            app.logger.info('{} is a valid host'.format(hostname))
        farmer = wk.get_worker(hostname, blockchain)
        utils.send_post(farmer, "/actions/", \
            { 'service': 'networking', 'action': 'add_connection', 'blockchain': blockchain, 'connection': connection}, \
            debug=False).content
    except requests.exceptions.RequestException as e:
        app.logger.info(traceback.format_exc())
        flash('Failed to connect to worker to add connection. Please check logs.', 'danger')
        flash(str(e), 'warning')
    except Exception as ex:
        app.logger.info(traceback.format_exc())
        flash('Invalid connection "{0}" provided.  Must be HOST:PORT.'.format(connection), 'danger')
        flash(str(ex), 'warning')
    else:
        flash('Connection added to {0} and sync engaging!'.format(blockchain), 'success')

def remove_connection(node_ids, hostname, blockchain):
    try:
        farmer = wk.get_worker(hostname, blockchain)
        utils.send_post(farmer, "/actions/", \
            { 'service': 'networking', 'action':'remove_connection', 'blockchain': blockchain, 'node_ids': node_ids }, \
            debug=False).content
    except requests.exceptions.RequestException as e:
        app.logger.info(traceback.format_exc())
        flash('Failed to connect to worker to add connection. Please check logs.', 'danger')
        flash(str(e), 'warning')
    except Exception as ex:
        app.logger.info(traceback.format_exc())
        flash('Unknown error occurred attempting to remove connections. Please check logs.', 'danger')
        flash(str(ex), 'warning')
    else:
        flash('Connection removed from {0}!'.format(blockchain), 'success')

def load_cold_wallet_addresses():
    data = {}
    if os.path.exists(COLD_WALLET_ADDRESSES_FILE):
        try:
            with open(COLD_WALLET_ADDRESSES_FILE) as f:
                data = json.load(f)
        except Exception as ex:
            msg = "Unable to read addresses from {0} because {1}".format(COLD_WALLET_ADDRESSES_FILE, str(ex))
            app.logger.error(msg)
            flash(msg, 'danger')
            return data
    return data
    
def save_cold_wallet_addresses(blockchain, cold_wallet_addresses):
    data = load_cold_wallet_addresses()
    if cold_wallet_addresses.strip():
        data[blockchain] = cold_wallet_addresses.split(',')
    else:
        del data[blockchain]
    try:
        with open(COLD_WALLET_ADDRESSES_FILE, 'w') as f:
            json.dump(data, f)
        flash(f'Successfully stored cold wallet addresses for {blockchain}. Please allow a few minutes for updated values to appear below.', 'success')
    except Exception as ex:
        msg = "Failed to store addresses in {0} because {1}".format(COLD_WALLET_ADDRESSES_FILE, str(ex))
        app.logger.error(msg)
        flash(msg, 'danger')
        return

def check(plot_id):
    check_file = '/root/.chia/plotman/checks/{0}.log'.format(plot_id)
    if os.path.exists(check_file):
        with open(check_file, 'r+') as fp:
            return fp.read()
    return make_response("Sorry, no plot check log found.  Please wait for scheduled plot check to run.", 200)
