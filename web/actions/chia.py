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

from flask_babel import _, lazy_gettext as _l
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
from web.models.chia import FarmSummary, FarmPlots, Wallets, Transactions, \
    Blockchains, Connections, Keys, ChallengesChartData, Summaries
from . import worker as wk
from . import stats

COLD_WALLET_ADDRESSES_FILE = '/root/.chia/machinaris/config/cold_wallet_addresses.json'

def load_farm_summary():
    farms = db.session.query(f.Farm).order_by(f.Farm.hostname).all()
    wallets = db.session.query(w.Wallet).order_by(w.Wallet.blockchain).all()
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
    chart_end_time = (datetime.datetime.now() - datetime.timedelta(minutes=2)).strftime("%Y-%m-%d %H:%M:%S.000")
    for blockchain in farm_summary.farms:
        challenges = db.session.query(c.Challenge).filter(c.Challenge.blockchain==blockchain,
            c.Challenge.created_at >= chart_start_time,
            c.Challenge.created_at <= chart_end_time).order_by(
            c.Challenge.created_at.desc(), c.Challenge.hostname).all()
        farm_summary.farms[blockchain]['challenges'] = ChallengesChartData(challenges)

def load_wallets():
    wallets = db.session.query(w.Wallet).order_by(w.Wallet.blockchain).all()
    cold_wallet_addresses = load_cold_wallet_addresses()
    return Wallets(wallets, cold_wallet_addresses)

def load_blockchains():
    try:  
        blockchains = db.session.query(b.Blockchain).order_by(b.Blockchain.blockchain).all()
        return Blockchains(blockchains)
    except Exception as ex:
        app.logger.error("Error querying for blockchains: {0}".format(str(ex)))
    return None

def load_summaries():
    app.logger.debug("Loading Summary page data...")
    try:
        blockchains = load_blockchains()
        app.logger.debug("Found {0} blockchains states for summary page.".format(len(blockchains.rows)))
        farms = load_farm_summary()
        app.logger.debug("Found {0} blockchain farms for summary page.".format(len(farms.farms)))
        summary_stats = stats.load_summary_stats(blockchains.rows)
        app.logger.debug("Found {0} blockchain stats.".format(len(summary_stats)))
        return Summaries(blockchains, farms.farms, farms.wallets, summary_stats)
    except Exception as ex:
        app.logger.error("Error loading summary: {0}".format(str(ex)))
        traceback.print_exc()
    return None

def load_connections(lang='en'):
    connections = db.session.query(co.Connection).all()
    return Connections(connections, lang)

def load_keys():
    keys = db.session.query(k.Key).order_by(k.Key.blockchain).all()
    return Keys(keys)
    
def load_farmers():
    farmers = wk.load_worker_summary().farmers_harvesters()
    for farmer in farmers:
        app.logger.info("Load farmer statistics for {0}".format(farmer.displayname))
        farmer.plot_counts = str(stats.count_plots_by_ksize(farmer.hostname))[1:-1].replace("'", "")
        farmer.plot_types = str(stats.count_plots_by_type(farmer.hostname))[1:-1].replace("'", "")
        farmer.drive_count = stats.count_drives(farmer.hostname)
    return farmers

def load_config(farmer, blockchain):
    return utils.send_get(farmer, "/configs/farming/"+ blockchain, debug=False).content

def save_config(farmer, blockchain, config):
    try: # Validate the YAML first
        yaml.safe_load(config)
    except Exception as ex:
        app.logger.info(traceback.format_exc())
        flash(_('Updated config.yaml failed validation! Fix and save or refresh page.'), 'danger')
        flash(str(ex), 'warning')
    try:
        utils.send_put(farmer, "/configs/farming/" + blockchain, config, debug=False)
    except Exception as ex:
        flash(_('Failed to save config to farmer.  Please check log files.'), 'danger')
        flash(str(ex), 'warning')
    else:
        flash(_('Nice! Farming config validated and saved successfully. Worker services now restarting. Please allow 15 minutes to take effect.'), 'success')

def generate_key(key_path, blockchain):
    chia_binary = globals.get_blockchain_binary(blockchain)
    if os.path.exists(key_path) and os.stat(key_path).st_size > 0:
        app.logger.info('Skipping key generation as file exists and is NOT empty! {0}'.format(key_path))
        flash(_('Skipping key generation as file exists and is NOT empty!'), 'danger')
        flash(_('In-container path:') +  ' {0}'.format(key_path), 'warning')
        return False
    proc = Popen("{0} keys generate".format(chia_binary), stdout=PIPE, stderr=PIPE, shell=True)
    try:
        outs, errs = proc.communicate(timeout=90)
    except TimeoutExpired as ex:
        proc.kill()
        proc.communicate()
        app.logger.info(traceback.format_exc())
        flash(_('Timed out while generating keys!'), 'danger')
        flash(str(ex), 'warning')
        return False
    if errs:
        app.logger.info("{0}".format(errs.decode('utf-8')))
        flash(_('Unable to generate keys!'), 'danger')
        return False
    proc = Popen("{0} keys show --show-mnemonic-seed | tail -n 1 > {1}".format(chia_binary, key_path), stdout=PIPE, stderr=PIPE, shell=True)
    try:
        outs, errs = proc.communicate(timeout=90)
    except TimeoutExpired as ex:
        proc.kill()
        proc.communicate()
        app.logger.info(traceback.format_exc())
        flash(_('Timed out while generating keys!'), 'danger')
        flash(str(ex), 'warning')
        return False
    if errs:
        app.logger.info("{0}".format(errs.decode('utf-8')))
        flash(_('Unable to save mnemonic to') + ' {0}'.format(key_path), 'danger')
        return False
    else:
        app.logger.info("Store mnemonic output: {0}".format(outs.decode('utf-8')))
        try:
            mnemonic_words = open(key_path,'r').read().split()
            if len(mnemonic_words) != 24:
                flash('{0} '.format(key_path) + _('does not contain a 24-word mnemonic!'), 'danger')
                return False
        except:
                flash('{0} '.format(key_path) + _('was unreadable or not found.'), 'danger')
                return False
        flash(_('Welcome! A new key has been generated, see below. Please visit the %(link_open)sWiki%(link_close)s to get started with Machinaris. Please allow 15 minutes for Chia to begin syncing with peers.', 
            link_open='<a href="https://github.com/guydavis/machinaris/wiki#basic-configuration" target="_blank">', link_close='</a>'), 'success')
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
        flash(_('Timed out while starting farmer! Try restarting the Machinaris container.'), 'danger')
        flash(str(ex), 'warning')
        return False
    if errs:
        app.logger.info("{0}".format(errs.decode('utf-8')))
        flash(_('Unable to start farmer. Try restarting the Machinaris container.'), 'danger')
        return False
    return True

def import_key(key_path, mnemonic, blockchain):
    chia_binary = globals.get_blockchain_binary(blockchain)
    if len(mnemonic.strip().split()) != 24:
        flash(_('Did not receive a 24-word mnemonic seed phrase!'), 'danger')
        return False
    if os.path.exists(key_path) and os.stat(key_path).st_size > 0:
        app.logger.info('Skipping key import as file exists and is NOT empty! {0}'.format(key_path))
        flash(_('Skipping key import as file exists and is NOT empty!'), 'danger')
        flash(_('In container path:') + ' {0}'.format(key_path), 'warning')
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
        flash(_('Timed out while adding key!'), 'danger')
        flash(str(ex), 'warning')
        return False
    if errs:
        app.logger.info("{0}".format(errs.decode('utf-8')))
        flash(_('Unable to import provided mnemonic seed phrase!'), 'danger')
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
        flash(_('Timed out while starting farmer! Try restarting the Machinaris container.'), 'danger')
        flash(str(ex), 'warning')
        return False
    if errs:
        app.logger.info("{0}".format(errs.decode('utf-8')))
        flash(_('Unable to start farmer. Try restarting the Machinaris container.'), 'danger')
        return False
    if outs:
        app.logger.debug(outs.decode('utf-8'))
    flash(_('Welcome! Your mnemonic key was imported. Please visit the %(link_open)sWiki%(link_close)s to get started with Machinaris. Please allow 15 minutes for Chia to begin syncing with peers.', 
            link_open='<a href="https://github.com/guydavis/machinaris/wiki#basic-configuration" target="_blank">', link_close='</a>'), 'success')
    return True

def add_connections(connections, hostname, blockchain):
    farmer = wk.get_worker(hostname, blockchain)
    try:
        for connection in connections:
            host,port = connection.split(':')
            if socket.gethostbyname(host) == host:
                app.logger.info('{} is a valid IP address'.format(host))
            elif socket.gethostbyname(host) != host:
                app.logger.info('{} is a valid host'.format(hostname))
    except requests.exceptions.RequestException as e:
        app.logger.info(traceback.format_exc())
        flash(_('Failed to connect to worker to add connection. Please check logs.'), 'danger')
        flash(str(e), 'warning')
    except Exception as ex:
        app.logger.info(traceback.format_exc())
        flash(_('Invalid connection "%(connection)s" provided. Must be HOST:PORT.', connection=connection), 'danger')
        flash(str(ex), 'warning')
    try: # Send request, but timeout in only a second while API works in background
        utils.send_post(farmer, "/actions/", \
            { 'service': 'networking', 'action': 'add_connections', 'blockchain': blockchain, \
            'connections': connections}, debug=False, timeout=1) 
    except requests.exceptions.ReadTimeout: 
        pass
    if len(connections) == 1:
        flash(_('Connection added to %(blockchain)s and sync engaging! Please wait a few minutes...', blockchain=blockchain.capitalize()), 'success')
    else:
        flash(_('Node peers from AllTheBlocks added to %(blockchain)s and sync engaging! Please wait a few minutes...', blockchain=blockchain.capitalize()), 'success')

def remove_connection(node_ids, hostname, blockchain):
    try:
        farmer = wk.get_worker(hostname, blockchain)
        utils.send_post(farmer, "/actions/", \
            { 'service': 'networking', 'action':'remove_connection', 'blockchain': blockchain, 'node_ids': node_ids }, \
            debug=False).content
    except requests.exceptions.RequestException as e:
        app.logger.info(traceback.format_exc())
        flash(_('Failed to connect to worker to add connection. Please check logs.'), 'danger')
        flash(str(e), 'warning')
    except Exception as ex:
        app.logger.info(traceback.format_exc())
        flash(_('Unknown error occurred attempting to remove connections. Please check logs.'), 'danger')
        flash(str(ex), 'warning')
    else:
        flash(_('Connection removed from') + ' {0}!'.format(blockchain), 'success')

def load_hot_wallet_addresses():
    hot_addresses = {}
    for key in load_keys().rows:
        hot_addresses[key['blockchain']] = key['addresses']
    return hot_addresses

def load_cold_wallet_addresses():
    data = {}
    if os.path.exists(COLD_WALLET_ADDRESSES_FILE):
        try:
            with open(COLD_WALLET_ADDRESSES_FILE) as f:
                data = json.load(f)
        except Exception as ex:
            msg = _("Unable to read addresses from %(file)s because %(exception)s", file=COLD_WALLET_ADDRESSES_FILE, exception=str(ex))
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
        flash(_('Successfully stored cold wallet addresses for %(blockchain)s. Please allow a few minutes for updated values to appear below.', blockchain=blockchain), 'success')
    except Exception as ex:
        msg = _("Unable to store addresses in %(file)s because %(exception)s", file=COLD_WALLET_ADDRESSES_FILE, exception=str(ex))
        app.logger.error(msg)
        flash(msg, 'danger')
        return

def check(plot_id):
    check_file = '/root/.chia/plotman/checks/{0}.log'.format(plot_id)
    if os.path.exists(check_file):
        with open(check_file, 'r+') as fp:
            return fp.read()
    return make_response(_("Sorry, no plot check log found. Please wait for scheduled plot check to run."), 200)

def get_transactions(lang, worker, blockchain, wallet_id):
    try:
        response = utils.send_get(worker, "/transactions/{0}".format(wallet_id), {}, debug=False, lang=lang)
        if response.status_code == 200:
            transactions = json.loads(response.content.decode('utf-8'))
            return Transactions(blockchain, transactions)
    except Exception as ex:
        app.logger.info('Failed to load transactions from {0}:{1} running {2} because {3}'.format(
                worker.hostname, worker.port, blockchain, str(ex)))
    return None

def load_wallet_ids(blockchain):
    if globals.legacy_blockchain(blockchain):
        return [{'id': '1', 'name': blockchain.capitalize() + ' ' + _('Wallet') }]
    wallet_ids = []
    wallet = db.session.query(w.Wallet).filter(w.Wallet.blockchain==blockchain).first()
    wallet_name = None
    for line in wallet.details.split('\n'):
        if line.strip().endswith(':') and not line.strip() == 'Connections:':
            wallet_name = line.strip()[:-1]
        elif line.strip().startswith('-Wallet ID:'):
            wallet_ids.append({'id': line.split(':')[1].strip(), 'name': wallet_name })
    return wallet_ids