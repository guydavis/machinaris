#
# CLI interactions with the blockchain binaries which support "official" pools
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
from common.config import globals
from common.models import plotnfts as pn, pools as po, wallets as w, partials as pr, workers as wkrs
from common.utils import converters
from web.models.pools import Plotnfts, Pools, PoolConfigs, PartialsChartData
from . import worker as wk

def load_plotnfts():
    plotnfts = db.session.query(pn.Plotnft).all()
    return Plotnfts(plotnfts)

def load_plotnfts_by_blockchain(blockchain):
    plotnfts = db.session.query(pn.Plotnft).filter(pn.Plotnft.blockchain==blockchain).all()
    return Plotnfts(plotnfts)

def load_pools():
    plotnfts = db.session.query(pn.Plotnft).all()
    pools = db.session.query(po.Pool).order_by(po.Pool.blockchain).all()
    return Pools(pools, plotnfts)

def get_plotnft_log():
    try:
        return open('/root/.{0}/mainnet/log/plotnft.log'.format(os.environ['blockchains']),"r").read()
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

def send_request(fullnode, selected_blockchain, launcher_ids, choices, pool_urls, wallet_nums,current_pool_urls):
    app.logger.info("Sending pooling settings change request...")
    try:
        response = utils.send_post(fullnode, "/actions/", 
            payload={
                    "service": "pooling","action": "save", "blockchain": selected_blockchain, 
                        "choices": choices, "pool_urls": pool_urls, "current_pool_urls": current_pool_urls,
                        "launcher_ids": launcher_ids, "wallet_nums": wallet_nums
                    }, 
            debug=True)
    except:
        app.logger.info(traceback.format_exc())
        flash(_('Failed to update Pool settings! Please check the logs from the Workers page.'), 'danger')
    else:
        if response.status_code == 200:
            flash(response.content.decode('utf-8'), 'message')
        else:
            flash(response.content.decode('utf-8'), 'danger')

def get_pool_configs():
    configs = {}
    for blockchain in po.POOLABLE_BLOCKCHAINS:
        plotnfts = db.session.query(pn.Plotnft).filter(pn.Plotnft.blockchain == blockchain).all()
        wallets = db.session.query(w.Wallet).filter(w.Wallet.blockchain == blockchain).all()
        configs[blockchain] = PoolConfigs(blockchain, plotnfts, wallets)
    return configs

def partials_chart_data(farm_summary):
    for blockchain in farm_summary.farms:
        # Only pull partials found up to the start of the hour, exactly 23 hours before current hour
        # This excludes counting partials in same hour exactly 24 hours ago in current hour
        start_time = (datetime.datetime.now().replace(microsecond=0, second=0, minute=0) - datetime.timedelta(hours=23)).strftime("%Y-%m-%d %H:%M:%S")
        app.logger.debug("Counting partials starting at {0} and later...".format(start_time))
        partials = db.session.query(pr.Partial).filter(pr.Partial.blockchain==blockchain,pr.Partial.created_at>=start_time).order_by(pr.Partial.created_at.desc()).all()
        farm_summary.farms[blockchain]['partials'] =  PartialsChartData(partials)

def get_unclaimed_plotnft_rewards():
    rewards = {}
    for wkr in db.session.query(wkrs.Worker).filter(wkrs.Worker.mode=='fullnode').order_by(wkrs.Worker.blockchain).all():
        if wkr.connection_status() == 'Responding':
            total_coins = 0.0
            try:
                rewards_by_launcher_id = json.loads(utils.send_get(wkr, '/rewards/', {}, debug=False).content)
                for launcher_id in rewards_by_launcher_id.keys():
                    for coin in rewards_by_launcher_id[launcher_id]:
                        total_coins += float(coin['amount'])
            except Exception as ex:
                app.logger.error("Failed to query for {0} recoverable rewards due to {1}.".format(wkr.blockchain, str(ex)))
            #if total_coins > 0: # Only show if recoverable rewards are available
            rewards[wkr.blockchain.capitalize() + '|' + wkr.hostname] = "{0} {1}".format(
                converters.round_balance(total_coins),
                globals.get_blockchain_symbol(wkr.blockchain).lower()
            )
    return rewards
    
def request_unclaimed_plotnft_reward_recovery():
    wallet = db.session.query(w.Wallet).filter(w.Wallet.blockchain == 'chia').first()
    if not wallet:
        flash("Found no Chia wallet details during reward recovery.  Just starting up?", 'error')
        return
    wallet_id = wallet.wallet_id()
    if not wallet_id: 
        flash("Found no wallet id, so skipping NFT 7/8 reward recovery.", 'error')
        return
    plotnfts = db.session.query(pn.Plotnft).filter(pn.Plotnft.blockchain == 'chia').all()
    if len(plotnfts) == 0:
        flash("Found no Chia PlotNFTs at all, so skipping NFT 7/8 reward recovery as unnecessary.", 'error')
        return
    for plotnft in plotnfts:
        if not plotnft.launcher: 
            app.logger.info("Found no launcher id, so skipping NFT 7/8 reward recovery on plotnft: {0}".format(plotnft))
            continue
        pool_contract_address = plotnft.pool_contract_address()
        if not pool_contract_address: 
            app.logger.info("Found no pool contract address, so skipping NFT 7/8 reward recovery on plotnft: {0}".format(plotnft))
            continue
        for wkr in db.session.query(wkrs.Worker).filter(wkrs.Worker.mode == 'fullnode', 
            wkrs.Worker.blockchain != 'chia', wkrs.Worker.blockchain != 'chives', wkrs.Worker.blockchain != 'mmx').order_by(wkrs.Worker.blockchain).all():
            if wkr.connection_status() == 'Responding':
                payload = {
                    'blockchain': wkr.blockchain,
                    'wallet_id': wallet_id,
                    'launcher_id': plotnft.launcher,
                    'pool_contract_address': pool_contract_address
                }
                try:
                    utils.send_post(wkr, '/rewards/', payload, debug=True)
                except Exception as ex:
                    app.logger.error("Failed to request {0} reward recovery due to {1}.".format(wkr.blockchain, str(ex)))
    flash(_("Reward recovery for portable plots has been initiated.  Tomorrow, please check the Total Balance charts below for each blockchain with recoverable coins."))
        