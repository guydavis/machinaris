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
from stat import S_ISREG, ST_CTIME, ST_MTIME, ST_MODE, ST_SIZE
from subprocess import Popen, TimeoutExpired, PIPE
from sqlalchemy import or_
from os import path

from web import app, db, utils
from common.models import farms as f, plots as p, challenges as c, wallets as w, \
    blockchains as b, connections as co, keys as k, plotnfts as pn, pools as po, \
    partials as pr
from common.config import globals
from web.models.chia import FarmSummary, FarmPlots, Wallets, \
    Blockchains, Connections, Keys, Plotnfts, Pools, PartialsChartData, \
    ChallengesChartData, PLOT_TABLE_COLUMNS
from . import worker as wk

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

def partials_chart_data(farm_summary):
    for blockchain in farm_summary.farms:
        partials = db.session.query(pr.Partial).filter(pr.Partial.blockchain==blockchain).order_by(pr.Partial.created_at.desc()).all()
        farm_summary.farms[blockchain]['partials'] =  PartialsChartData(partials)

def load_wallets():
    wallets = db.session.query(w.Wallet).order_by(w.Wallet.blockchain).all()
    return Wallets(wallets)

def load_blockchain_show():
    try:  # Sparkly had an error here once with malformed data
        blockchains = db.session.query(b.Blockchain).order_by(b.Blockchain.blockchain).all()
        return Blockchains(blockchains)
    except:
        traceback.print_exc()
    return None

def load_connections_show():
    connections = db.session.query(co.Connection).all()
    return Connections(connections)

def load_keys_show():
    keys = db.session.query(k.Key).order_by(k.Key.blockchain).all()
    return Keys(keys)

def load_plotnfts():
    plotnfts = db.session.query(pn.Plotnft).all()
    return Plotnfts(plotnfts)

def load_pools():
    plotnfts = db.session.query(pn.Plotnft).all()
    pools = db.session.query(po.Pool).all()
    return Pools(pools, plotnfts)

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

def check_plots(worker, first_load):
    try:
        payload = {"service":"farming", "action":"check_plots", "first_load": first_load }
        response = utils.send_post(worker, "/analysis/", payload, debug=False)
        return response.content.decode('utf-8')
    except:
        app.logger.info(traceback.format_exc())
        flash('Failed to check plots on {0}. Please see logs.'.format(worker.hostname), 'danger')

def get_plotnft_log():
    try:
        return open('/root/.chia/mainnet/log/plotnft.log',"r").read()
    except:
        return None

def get_first_pool_wallet_id():
    for plotnft in load_plotnfts().rows:
        for line in plotnft['details'].splitlines():
            app.logger.info(line)
            m = re.search("Wallet id (\d+):", line)
            if m:
                return m.group(1)
    return None

def process_pool_save(choice, pool_url, current_pool_url):
    pool_wallet_id = get_first_pool_wallet_id()
    if choice == "self":
        if current_pool_url and pool_wallet_id:
            return process_pool_leave(choice, pool_wallet_id)
        elif not pool_wallet_id:
            return process_self_pool()
        else:
            flash('Already self-pooling your own NFT.  No changes made.', 'message')
            return False
    elif choice == "join":
        if current_pool_url == pool_url:
            flash('Already pooling with {0}.  No changes made.'.format(pool_url), 'message')
            return False
        return process_pool_join(choice, pool_url, pool_wallet_id)

def process_pool_leave(choice, wallet_index):
    chia_binary = globals.get_blockchain_binary('chia')
    cmd = "{0} plotnft leave -y -i {1}".format(chia_binary, wallet_index)
    app.logger.info("Attempting to leave pool: {0}".format(cmd))
    result = ""
    try:
        child = pexpect.spawn(cmd)
        child.logfile = sys.stdout.buffer
        while True:
            i = child.expect(["Choose wallet key:.*\r\n", pexpect.EOF])
            if i == 0:
                app.logger.info("plotnft got index prompt so selecting #{0}".format(wallet_index))
                child.sendline("{0}".format(wallet_index))
            elif i==1:
                app.logger.info("plotnft end of output...")
                result += child.before.decode("utf-8") + child.read().decode("utf-8")
                break
        if result:  # Chia outputs their errors to stdout, not stderr, so must check.
            stdout_lines = result.splitlines()
        out_file = '/root/.chia/mainnet/log/plotnft.log'
        with open(out_file, 'a') as f:
            f.write("\nchia plotnft plotnft leave -y -i 1 --> Executed at: {0}\n".format(time.strftime("%Y%m%d-%H%M%S")))
            for line in stdout_lines:
                f.write(line)
            f.write("\n**********************************************************************\n")
        for line in stdout_lines:
            if "Error" in line:
                flash('Error while leaving Chia pool.', 'danger')
                flash(line, 'warning')
                return False
    except Exception as ex:
        app.logger.info(traceback.format_exc())
        print(str(child))
        flash(str(ex), 'danger')
        return False
    time.sleep(15)
    try: # Trigger a status update
        requests.get("http://localhost:8927/plotnfts/", timeout=5)
    except:
        app.logger.info(traceback.format_exc())
    time.sleep(5)
    flash('Successfully left pool, switching to self plotting.  Please wait a while to complete, then refresh page. See below for details.', 'success')
    return True

def process_pool_join(choice, pool_url, pool_wallet_id):
    chia_binary = globals.get_blockchain_binary('chia')
    app.logger.info("Attempting to join pool at URL: {0} with wallet_id: {1}".format(pool_url, pool_wallet_id))
    try:
        if not pool_url.strip():
            raise Exception("Empty pool URL provided.")
        if not pool_url.startswith('https://') and not pool_url.startswith('http://'):
            pool_url = "https://" + pool_url
        result = urllib.parse.urlparse(pool_url)
        if result.scheme != 'https':
            raise Exception("Non-HTTPS scheme provided.")
        if not result.netloc:
            raise Exception("No hostname or IP provided.")
    except Exception as ex:
        app.logger.info(traceback.format_exc())
        flash('{0}'.format(str(ex)), 'danger')
        return False
    if pool_wallet_id: # Just joining a pool with existing NFT
        cmd = "{0} plotnft join -y -u {1} -i {2}".format(chia_binary, pool_url, pool_wallet_id)
        wallet_index = pool_wallet_id
    else:  # Both creating NFT and joining pool in one setp
        cmd = "{0} plotnft create -y -u {1} -s pool".format(chia_binary, pool_url)
        wallet_index = 1
    app.logger.info("Executing: {0}".format(cmd))
    result = ""
    try:
        child = pexpect.spawn(cmd)
        child.logfile = sys.stdout.buffer
        while True:
            i = child.expect(["Choose wallet key:.*\r\n", pexpect.EOF])
            if i == 0:
                app.logger.info("plotnft got index prompt so selecting #{0}".format(wallet_index))
                child.sendline("{0}".format(wallet_index))
            elif i==1:
                app.logger.info("plotnft end of output...")
                result += child.before.decode("utf-8") + child.read().decode("utf-8")
                break
        if result:  # Chia outputs their errors to stdout, not stderr, so must check.
            stdout_lines = result.splitlines()
            out_file = '/root/.chia/mainnet/log/plotnft.log'
            with open(out_file, 'a') as f:
                f.write("\n{0} --> Executed at: {1}\n".format(cmd, time.strftime("%Y%m%d-%H%M%S")))
                for line in stdout_lines:
                    f.write(line)
                f.write("\n**********************************************************************\n")
            for line in stdout_lines:
                if "Error" in line:
                    flash('Error while joining Chia pool. Please double-check pool URL: {0}'.format(pool_url), 'danger')
                    flash(line, 'warning')
                    return False
    except Exception as ex:
        app.logger.info(traceback.format_exc())
        print(str(child))
        flash(str(ex), 'danger')
        return False
    time.sleep(15)
    try: # Trigger a status update
        requests.get("http://localhost:8927/plotnfts/", timeout=5)
    except:
        app.logger.info(traceback.format_exc())
    time.sleep(5)
    flash('Successfully joined {0} pool by creating Chia NFT.  Please wait a while to complete, then refresh page. See below for details.'.format(pool_url), 'success')
    return True

def process_self_pool(wallet_index=1):
    chia_binary = globals.get_blockchain_binary('chia')
    cmd = "{0} plotnft create -y -s local".format(chia_binary)
    app.logger.info("Attempting to create NFT for self-pooling. {0}".format(cmd))
    result = ""
    try:
        child = pexpect.spawn(cmd)
        child.logfile = sys.stdout.buffer
        while True:
            i = child.expect(["Choose wallet key:.*\r\n", pexpect.EOF])
            if i == 0:
                app.logger.info("plotnft got index prompt so selecting #{0}".format(wallet_index))
                child.sendline("{0}".format(wallet_index))
            elif i==1:
                app.logger.info("plotnft end of output...")
                result += child.before.decode("utf-8") + child.read().decode("utf-8")
                break
        if result:  # Chia outputs their errors to stdout, not stderr, so must check.
            stdout_lines = result.splitlines()
        out_file = '/root/.chia/mainnet/log/plotnft.log'
        with open(out_file, 'a') as f:
            f.write("\n{0} --> Executed at: {1}\n".format(cmd, time.strftime("%Y%m%d-%H%M%S")))
            for line in stdout_lines:
                f.write(line)
            f.write("\n**********************************************************************\n")
        for line in stdout_lines:
            if "Error" in line:
                flash('Error while creating self-pooling NFT', 'danger')
                flash(line, 'warning')
                return False
    except Exception as ex:
        app.logger.info(traceback.format_exc())
        print(str(child))
        flash(str(ex), 'danger')
        return False
    time.sleep(15)
    try: # Trigger a status update
        requests.get("http://localhost:8927/plotnfts/", timeout=5)
    except:
        app.logger.info(traceback.format_exc())
    time.sleep(5)
    flash('Successfully created a NFT for self-pooling.  Please wait a while to complete, then refresh page. See below for details.', 'success')
    return True
