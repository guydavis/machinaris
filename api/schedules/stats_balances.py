#
# Store the total wallet balance (hot + cold) per blockchain locally on the controller each hour.
#

from ast import Store
import datetime
import http
import json
from locale import currency
import os
import requests
import socket
import sqlite3
import traceback

from flask import g

from common.config import globals
from common.models import stats, wallets as w
from common.utils import converters, fiat
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
            fiat_total = 0.0
            currency_symbol = fiat.get_local_currency_symbol().lower()
            cold_wallet_balance_error = False
            for wallet in wallets.rows:
                if wallet['fiat_balance']:
                    fiat_total += float(wallet['fiat_balance'])
                if wallet['cold_balance']:  # Valid number, may be zero if no cold wallet addresses
                    store_balance_locally(wallet['blockchain'], wallet['total_balance'], current_datetime)
                else: # A None value indicates cold wallet addresses which gave error on balance websvc call
                    cold_wallet_balance_error = True  # Skip recording a balance data point for this blockchain
                    app.logger.error("No wallet balance recorded. Received an erroneous cold wallet balance for {0} wallet. Please correct the address and verify at https://alltheblocks.net".format(wallet['blockchain']))
                    continue # Don't save a data point if part of the sum is missing due to error
            app.logger.info("Fiat total is {0} {1}".format(round(fiat_total, 2), currency_symbol))
            if not cold_wallet_balance_error: # Don't record a total across all wallets if one is temporarily erroring out
                store_total_locally(round(fiat_total, 2), currency_symbol, current_datetime)
        except:
            app.logger.info("Failed to load and store wallet balance.")
            app.logger.info(traceback.format_exc())

def store_balance_locally(blockchain, wallet_balance, current_datetime):
    try:
        db.session.add(stats.StatWalletBalances(
            hostname=utils.get_hostname(),
            blockchain=blockchain,
            value = wallet_balance,
            created_at=current_datetime))
    except:
        app.logger.info(traceback.format_exc())
    db.session.commit()

def store_total_locally(total_balance, currency_symbol, current_datetime):
    try:
        db.session.add(stats.StatTotalBalance(
            hostname=utils.get_hostname(),
            value = total_balance,
            currency = currency_symbol,
            created_at=current_datetime))
    except:
        app.logger.info(traceback.format_exc())
    db.session.commit()