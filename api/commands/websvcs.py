#
# Access to public web APIs
#

import bs4
import datetime
import http
import json
import os
import requests
import socket

from api import app

ALLTHEBLOCKS_REQUEST_INTERVAL_MINS = 15
COLD_WALLET_ADDRESSES_FILE = '/root/.chia/machinaris/config/cold_wallet_addresses.json'
COLD_WALLET_CACHE_FILE = '/root/.chia/machinaris/cache/cold_wallet_cache.json'
BLOCKCHAIN_PRICES_CACHE_FILE = '/root/.chia/machinaris/cache/blockchain_prices_cache.json'
EXCHANGE_RATES_CACHE_FILE = '/root/.chia/machinaris/cache/exchange_rates_cache.json'

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
            msg = "Unable to read cold wallet cache from {0} because {1}".format(COLD_WALLET_CACHE_FILE, str(ex))
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

def request_cold_wallet_balance(blockchain, cold_wallet_cache, alltheblocks_blockchain, address, debug=False):
    app.logger.info("Requesting {0} wallet balance for {1}".format(alltheblocks_blockchain, address))
    url = f"https://api.alltheblocks.net/{alltheblocks_blockchain}/address/{address}"
    try:
        if debug:
            http.client.HTTPConnection.debuglevel = 1
        response = json.loads(requests.get(url).content)
        balance = response['balance'] / MOJO_PER_COIN[blockchain]
        cold_wallet_cache[address] = balance  # Save last good response from websvc
        app.logger.info("Received cold wallet balance of {0}".format(balance))
        http.client.HTTPConnection.debuglevel = 0
        return balance
    except Exception as ex:
        app.logger.info("Failed to query {0} due to {1}".format(url, str(ex)))
        return None

last_cold_wallet_request_time = None
def cold_wallet_balance(blockchain):
    global last_cold_wallet_request_time
    total_balance = 0.0
    alltheblocks_blockchain = get_alltheblocks_name(blockchain)
    addresses_per_blockchain = load_cold_wallet_addresses()
    cold_wallet_cache = load_cold_wallet_cache()
    if blockchain in addresses_per_blockchain:
        if not last_cold_wallet_request_time or last_cold_wallet_request_time <= \
                (datetime.datetime.now() - datetime.timedelta(minutes=ALLTHEBLOCKS_REQUEST_INTERVAL_MINS)):
            for address in addresses_per_blockchain[blockchain]:
                total_balance += request_cold_wallet_balance(blockchain, cold_wallet_cache, alltheblocks_blockchain, address)
            save_cold_wallet_cache(cold_wallet_cache)
            last_cold_wallet_request_time = datetime.datetime.now()
            return total_balance
        else:
            for address in addresses_per_blockchain[blockchain]:
                if address in cold_wallet_cache:
                    cached_cold_balance = float(cold_wallet_cache[address])
                    #app.logger.info("Using previous cold wallet balance of {0} which may be stale.".format(cached_cold_balance))
                    total_balance += cached_cold_balance
            return total_balance
    return '' # No cold wallet addresses to check

def load_prices_cache():
    data = {}
    if os.path.exists(BLOCKCHAIN_PRICES_CACHE_FILE):
        try:
            with open(BLOCKCHAIN_PRICES_CACHE_FILE) as f:
                data = json.load(f)
        except Exception as ex:
            msg = "Unable to read price cache from {0} because {1}".format(BLOCKCHAIN_PRICES_CACHE_FILE, str(ex))
            app.logger.error(msg)
            return data
    return data

def save_prices_cache(data):
    try:
        with open(BLOCKCHAIN_PRICES_CACHE_FILE, 'w') as f:
            json.dump(data, f)
    except Exception as ex:
        app.logger.error("Failed to store prices cache in {0} because {1}".format(BLOCKCHAIN_PRICES_CACHE_FILE, str(ex)))

def request_prices(prices, debug=False):
    url = "https://alltheblocks.net"
    app.logger.info("Requesting recent pricing for blockchains from {0}".format(url))
    if debug:
        http.client.HTTPConnection.debuglevel = 1
    data = requests.get(url).text
    http.client.HTTPConnection.debuglevel = 0
    soup = bs4.BeautifulSoup(data, 'html.parser')
    table = soup.find('table', class_="table b-table table-sm")
    for row in table.tbody.find_all('tr'):
        if 'data-pk' in row.attrs:
            blockchain = row['data-pk'].replace('stai', 'staicoin')
            price_column = row.find('td', class_='text-right')
            if len(price_column.contents) == 1:
                price_value = price_column.contents[0].string.strip()
                if price_value.startswith('$'):
                    #app.logger.info("{0} @ {1}".format(blockchain, price_value[1:].strip()))
                    try:
                        prices[blockchain] = float(price_value[1:].strip())
                    except Exception as ex:
                        app.logger.info("Failed to parse a decimal number from {0}".format(price_value[1:].strip()))
                else:
                    #app.logger.info("No price found for blockchain: {0}".format(blockchain))
                    pass
    return prices

last_price_request_time = None
def get_prices():
    global last_price_request_time
    prices = load_prices_cache()
    if not last_price_request_time or last_price_request_time <= \
            (datetime.datetime.now() - datetime.timedelta(minutes=ALLTHEBLOCKS_REQUEST_INTERVAL_MINS)):
            request_prices(prices)
            last_price_request_time = datetime.datetime.now()
    save_prices_cache(prices)
    save_exchange_rates()
    return prices

def save_exchange_rates(debug=False):
    url = "https://api.coingecko.com/api/v3/exchange_rates"
    app.logger.info("Requesting exchange rates vs bitcoin from {0}".format(url))
    try:
        if debug:
            http.client.HTTPConnection.debuglevel = 1
        resp = requests.get(url)
        http.client.HTTPConnection.debuglevel = 0
        if resp.status_code == 200:
            data = json.loads(resp.text)
            with open(EXCHANGE_RATES_CACHE_FILE, 'w') as f:
                json.dump(data['rates'], f)
        else:
            app.logger.error("Received {0} from {1}".format(resp.status_code, url))
    except Exception as ex:
            app.logger.error("Failed to store exchange cache in {0} because {1}".format(EXCHANGE_RATES_CACHE_FILE, str(ex)))
 