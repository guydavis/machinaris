#
# Access to public web APIs
#

import http
import json
import os
import requests
import socket

from api import app

COLD_WALLET_ADDRESSES_FILE = '/root/.chia/machinaris/config/cold_wallet_addresses.json'

MOJO_PER_COIN = {
    'cactus': 1000000000000,
    'chia': 1000000000000, 
    'chives': 100000000,
    'cryptodoge': 1000000,
    'flax': 1000000000000,
    'flora': 1000000000000,
    'hddcoin': 1000000000000,
    'nchain': 1000000000000,
    'silicoin': 1000000000000, 
    'staicoin': 1000000000,
    'stor': 1000000000000,
}

def load_cold_wallet_addresses():
    data = {}
    if os.path.exists(COLD_WALLET_ADDRESSES_FILE):
        try:
            with open(COLD_WALLET_ADDRESSES_FILE) as f:
                data = json.load(f)
        except Exception as ex:
            msg = "Unable to read addresses from {0} because {1}".format(COLD_WALLET_ADDRESSES_FILE, str(ex))
            app.logger.error(msg)
            return data
    return data

def cold_wallet_balance(blockchain, debug=False):
    balance = 0.0
    addresses_per_blockchain = load_cold_wallet_addresses()
    if blockchain in addresses_per_blockchain:
        if debug:
            http.client.HTTPConnection.debuglevel = 1
        for address in addresses_per_blockchain[blockchain]:
            url = f"https://api.alltheblocks.net/{blockchain}/address/{address}"
            try:
                response = json.loads(requests.get(url).content)
                balance += response['balance'] / MOJO_PER_COIN[blockchain] 
            except Exception as ex:
                app.logger.info("Failed to query {0} due to {1}".format(url, str(ex)))
        http.client.HTTPConnection.debuglevel = 0
        return balance
    else:
        return '' # No cold wallet addresses to check
