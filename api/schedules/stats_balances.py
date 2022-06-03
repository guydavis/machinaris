#
# Store the total wallet balance (hot + cold) per blockchain locally on the controller each hour.
#

from ast import Store
import datetime
import http
import json
import os
import requests
import socket
import sqlite3
import traceback

from flask import g

from common.config import globals
from common.models import stats, wallets as w
from api.commands import chia_cli, websvcs
from api.models import chia
from api import app, utils, db

def collect():
    with app.app_context():
        gc = globals.load()
        if not gc['is_controller']:
            app.logger.info("Only collect wallet balances on controller.")
            return
        current_datetime = datetime.datetime.now().strftime("%Y%m%d%H%M")
        try:
            wallets = db.session.query(w.Wallet).order_by(w.Wallet.blockchain).all()
            cold_wallet_addresses = websvcs.load_cold_wallet_addresses()
            wallets = chia.Wallets(wallets, cold_wallet_addresses)
            for wallet in wallets.rows:
                store_locally(wallet['blockchain'], wallet['total_balance'], current_datetime)
        except:
            app.logger.info("Failed to load and store wallet balance.")
            app.logger.info(traceback.format_exc())

def store_locally(blockchain, wallet_balance, current_datetime):
    current_datetime = datetime.datetime.now().strftime("%Y%m%d%H%M")
    try:
        db.session.add(stats.StatWalletBalances(
            hostname=utils.get_hostname(),
            blockchain=blockchain,
            value = wallet_balance,
            created_at=current_datetime))
    except:
        app.logger.info(traceback.format_exc())
    db.session.commit()
