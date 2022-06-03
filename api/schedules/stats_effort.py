#
# Calculates effort per blockchain
#


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
from api.rpc import chia
from api import app, utils, db

def calculate():
    with app.app_context():
        gc = globals.load()
        current_datetime = datetime.datetime.now().strftime("%Y%m%d%H%M")
        try:
            wallets = chia.get_wallets()
            for wallet in wallets:
                print(wallet)
                app.logger.info("Getting transactions in wallet #{0}: {1}".format(wallet['id'], wallet['name']))
                chia.get_transactions(wallet['id'])
        except:
            app.logger.info("Failed to calculate blockchain effort.")
            app.logger.info(traceback.format_exc())
