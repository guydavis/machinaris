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
from common.models import plotnfts as pn, pools as po, wallets as w, partials as pr
from web.models.pools import Plotnfts, Pools, PoolConfigs, PartialsChartData
from . import worker as wk

def load_plotnfts():
    plotnfts = db.session.query(pn.Plotnft).all()
    return Plotnfts(plotnfts)

def load_plotnfts(blockchain):
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
        partials = db.session.query(pr.Partial).filter(pr.Partial.blockchain==blockchain).order_by(pr.Partial.created_at.desc()).all()
        farm_summary.farms[blockchain]['partials'] =  PartialsChartData(partials)
