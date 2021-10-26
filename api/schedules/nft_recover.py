#
# Performs a daily NFT wins recovery using fd-cli: https://github.com/Flora-Network/flora-dev-cli
#

import datetime
import os
import sqlite3
from subprocess import Popen, TimeoutExpired, PIPE
import traceback

from flask import g

from common.models import wallets as w, plotnfts as p
from common.config import globals
from api import app, utils

def execute():
    with app.app_context():
        from api import db
        gc = globals.load()
        if gc['is_controller']: # Only Chia fullnode should execute this
            wallet = db.session.query(w.Wallet).filter(w.Wallet.blockchain == 'chia').first()
            plotnfts = db.session.query(p.Plotnft).filter(p.Plotnft.blockchain == 'chia').all()
            wallet_id = wallet.wallet_id()
            if not wallet_id: 
                app.logger.info("Found no wallet id, so skipping NFT 7/8 win recovery.")
                return
            logfile = "/root/.chia/machinaris/logs/fd-cli.log"
            log_fd = os.open(logfile, os.O_RDWR | os.O_CREAT)
            log_fo = os.fdopen(log_fd, "a+")
            for plotnft in plotnfts:
                launcher_id = plotnft.launcher_id()
                if not launcher_id: 
                    app.logger.info("Found no launcher id, so skipping NFT 7/8 win recovery on plotnft: {0}".format(plotnft))
                    continue
                pool_contract_address = plotnft.pool_contract_address()
                if not pool_contract_address: 
                    app.logger.info("Found no pool contract address, so skipping NFT 7/8 win recovery on plotnft: {0}".format(plotnft))
                    continue
                vars = {}
                vars['FD_CLI_BC_DB_PATH'] = '/.chia/mainnet/db/blockchain_v1_mainnet.sqlite'
                vars['FD_CLI_WT_DB_PATH'] = '/.chia/mainnet/wallet/db/blockchain_wallet_v1_mainnet_{0}.sqlite'.format(wallet_id)
                fd_env = os.environ.copy()
                fd_env.update(vars)
                cmd = ["/usr/local/bin/fd-cli", "nft-recover"
                    "-l", launcher_id, "-p", pool_contract_address,
                    "-nh", "127.0.0.1", "-np", "18755",
                    "-ct", "/root/.chia/mainnet/config/ssl/full_node/private_full_node.crt"
                    "-ck", "/root/.chia/mainnet/config/ssl/full_node/private_full_node.key"
                    ]
                app.logger.info("Executing NFT 1/8 win recovery: {0}".format(cmd))
                proc = Popen(cmd,cwd="/fd-cli", env=fd_env, shell=True, universal_newlines=True, stdout=log_fo, stderr=log_fo)
                try:
                    outs, errs = proc.communicate(timeout=1800)
                except TimeoutExpired:
                    proc.kill()
                    proc.communicate()
                if errs:
                    app.logger.error(errs.decode('utf-8'))
                elif outs:
                    app.logger.info(outs.decode('utf-8'))
                else:
                    app.logger.error("Nothing returned from fd-cli call.")
