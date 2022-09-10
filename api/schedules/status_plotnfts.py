#
# Performs a REST call to controller (possibly localhost) of latest plotnft status.
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
from common.models import pools
from api.commands import pools_cli
from api import app
from api import utils

def extract_wallet_num(plotnft):
    for line in plotnft.split('\n'):
        if line.strip().startswith("Wallet id"):
            return int(line[len('Wallet id '): len(line)-2])
    return None

def extract_launcher_id(plotnft):
    for line in plotnft.split('\n'):
        if line.startswith("Launcher ID:"):
            return line.split(':')[1].strip()
    return None

def update():
    app.logger.info("Executing status_plotnfts...")
    with app.app_context():
        try:
            for blockchain in globals.enabled_blockchains():
                if not blockchain in pools.POOLABLE_BLOCKCHAINS:
                    continue
                hostname = utils.get_hostname()
                plotnfts = pools_cli.load_plotnft_show(blockchain)
                if plotnfts:
                    payload = []
                    for plotnft in plotnfts.wallets:
                        text = plotnft.replace('\r', '').strip()
                        if text:
                            launcher_id = extract_launcher_id(text)
                            payload.append({
                                "unique_id": hostname + '_' + blockchain + '_' + launcher_id,
                                "hostname": hostname,
                                "blockchain": blockchain,
                                # Note, for some reason sqlite/smorest refused inserts to column "launcher_id" so I shortened it
                                "launcher": launcher_id,
                                "wallet_num": extract_wallet_num(text),
                                "header": plotnfts.header.replace('\r', ''),
                                "details": text,
                            })
                    if len(payload):
                        utils.send_post('/plotnfts/', payload, debug=False)
                    else:
                        utils.send_delete('/plotnfts/{0}/{1}'.format(hostname, blockchain), debug=False)
                else:
                    app.logger.info("Not sending plotnft status as wallet is not running.")
        except Exception as ex:
            app.logger.info("Failed to load and send plotnft status because {0}".format(str(ex)))
