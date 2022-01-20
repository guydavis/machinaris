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
COLD_WALLET_CACHE_FILE = '/root/.chia/machinaris/config/cold_wallet_cache.json'

MOJO_PER_COIN = {
    'btcgreen': 1000000000000,
    'cactus': 1000000000000,
    'chia': 1000000000000, 
    'chives': 100000000,
    'cryptodoge': 1000000,
    'flax': 1000000000000,
    'flora': 1000000000000,
    'hddcoin': 1000000000000,
    'nchain': 1000000000000,
    'silicoin': 1000000000000, 
    'shibgreen': 1000,
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

def load_cold_wallet_cache():
    data = {}
    if os.path.exists(COLD_WALLET_CACHE_FILE):
        try:
            with open(COLD_WALLET_CACHE_FILE) as f:
                data = json.load(f)
        except Exception as ex:
            msg = "Unable to read cache from {0} because {1}".format(COLD_WALLET_CACHE_FILE, str(ex))
            app.logger.error(msg)
            return data
    return data

def save_cold_wallet_cache(cold_wallet_cache):
    try:
        with open(COLD_WALLET_CACHE_FILE, 'w') as f:
            json.dump(cold_wallet_cache, f)
    except Exception as ex:
        app.logger.error("Failed to store cold wallet cache in {0} because {1}".format(COLD_WALLET_CACHE_FILE, str(ex)))

def get_alltheblocks_name(blockchain):
    if blockchain == 'staicoin':
        return 'stai' # Special case for staicoin's inconsistent naming convention
    return blockchain

def cold_wallet_balance(blockchain, debug=False):
    total_balance = 0.0
    alltheblocks_blockchain = get_alltheblocks_name(blockchain)
    addresses_per_blockchain = load_cold_wallet_addresses()
    cold_wallet_cache = load_cold_wallet_cache()
    if blockchain in addresses_per_blockchain:
        if debug:
            http.client.HTTPConnection.debuglevel = 1
        for address in addresses_per_blockchain[blockchain]:
            url = f"https://api.alltheblocks.net/{alltheblocks_blockchain}/address/{address}"
            try:
                response = json.loads(requests.get(url).content)
                balance = response['balance'] / MOJO_PER_COIN[blockchain]
                cold_wallet_cache[address] = balance  # Save last good response from websvc
                total_balance += balance
            except Exception as ex:
                app.logger.info("Failed to query {0} due to {1}".format(url, str(ex)))
                if address in cold_wallet_cache:
                    cached_cold_balance = float(cold_wallet_cache[address])
                    app.logger.info("Using previous cold wallet balance of {0} WHICH MAY BE STALE!".format(cached_cold_balance))
                    total_balance += cached_cold_balance
        http.client.HTTPConnection.debuglevel = 0
        save_cold_wallet_cache(cold_wallet_cache)
        return total_balance
    else:
        return '' # No cold wallet addresses to check
