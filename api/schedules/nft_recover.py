#
# Performs a twice-daily NFT reward recovery using fd-cli: https://github.com/Flora-Network/flora-dev-cli
#

import datetime
import os
import sqlite3
import time
import traceback

from flask import g

from common.models import wallets as w, plotnfts as p, workers as wk
from common.config import globals
from api import app, utils

def execute():
    with app.app_context():
        from api import db
        gc = globals.load()
        if not gc['is_controller']: # Only Chia fullnode should gather launcher_ids and trigger recover on each fork
            return
        fullnodes = db.session.query(wk.Worker).filter(wk.Worker.mode == 'fullnode', 
            wk.Worker.blockchain != 'chia', wk.Worker.blockchain != 'chives').order_by(wk.Worker.blockchain).all()
        wallet = db.session.query(w.Wallet).filter(w.Wallet.blockchain == 'chia').first()
        plotnfts = db.session.query(p.Plotnft).filter(p.Plotnft.blockchain == 'chia').all()
        wallet_id = wallet.wallet_id()
        if not wallet_id: 
            app.logger.info("Found no wallet id, so skipping NFT 7/8 win recovery.")
            return
        for plotnft in plotnfts:
            launcher_id = plotnft.launcher_id()
            if not launcher_id: 
                app.logger.info("Found no launcher id, so skipping NFT 7/8 win recovery on plotnft: {0}".format(plotnft))
                continue
            pool_contract_address = plotnft.pool_contract_address()
            if not pool_contract_address: 
                app.logger.info("Found no pool contract address, so skipping NFT 7/8 win recovery on plotnft: {0}".format(plotnft))
                continue
            for fullnode in fullnodes:
                payload = {
                    'blockchain': fullnode.blockchain,
                    'wallet_id': wallet_id,
                    'launcher_id': launcher_id,
                    'pool_contract_address': pool_contract_address
                }
                utils.send_worker_post(fullnode, '/rewards/', payload, debug=True)
            