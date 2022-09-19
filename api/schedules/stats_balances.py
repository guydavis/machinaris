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

DELETE_OLD_STATS_AFTER_DAYS = 90

TABLES = [ stats.StatWalletBalances, stats.StatTotalBalance ]

def delete_old_stats():
    try:
        cutoff = datetime.datetime.now() - datetime.timedelta(days=DELETE_OLD_STATS_AFTER_DAYS)
        for table in TABLES:
            db.session.query(table).filter(table.created_at <= cutoff.strftime("%Y%m%d%H%M")).delete()
        db.session.commit()
    except:
        app.logger.info("Failed to delete old statistics.")
        app.logger.info(traceback.format_exc())

def collect():
    with app.app_context():
        gc = globals.load()
        if not gc['is_controller']:
            app.logger.info("Only collect wallet balances on controller.")
            return
        delete_old_stats()
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
            if wallet['blockchain'] == 'chia':
                app.logger.info("From {0} wallet rows, fiat total (including cold wallet balance) is {1} {2}".format(len(wallets.rows), round(fiat_total, 2), currency_symbol))
            if not cold_wallet_balance_error: # Don't record a total across all wallets if one is temporarily erroring out
                store_total_locally(round(fiat_total, 2), currency_symbol, current_datetime)
        except:
            app.logger.info("Failed to load and store wallet balance.")
            app.logger.info(traceback.format_exc())

def store_balance_locally(blockchain, wallet_balance, current_datetime):
    if blockchain == 'chia':
        app.logger.info("Storing Chia total wallet balance (including cold wallet balance) of {0}".format(wallet_balance))
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