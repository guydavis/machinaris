#
# Access to public web APIs
#

import bs4
import datetime
import http
import json
import os
import requests
import time
import traceback

from common.config import globals
from api import app

ALLTHEBLOCKS_REQUEST_INTERVAL_MINS = 15
COLD_WALLET_ADDRESSES_FILE = '/root/.chia/machinaris/config/cold_wallet_addresses.json'
COLD_WALLET_CACHE_FILE = '/root/.chia/machinaris/cache/cold_wallet_cache.json'
COLD_WALLET_CACHE_DIR = '/root/.chia/machinaris/cache/cold_wallets'
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

def save_cold_wallet_transactions(blockchain, address, cold_wallet_transactions):
    #app.logger.info("COLD TRANSACTIONS: {0}".format(cold_wallet_transactions))
    cache_dir =  COLD_WALLET_CACHE_DIR + '/' + blockchain
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
    cache_file = cache_dir + '/' + address + ".json"
    try:
        with open(cache_file, 'w') as f:
            json.dump(cold_wallet_transactions, f)
    except Exception as ex:
        app.logger.error("Failed to store cold wallet transactions in {0} because {1}".format(cache_file, str(ex)))

def request_cold_wallet_transactions_page(alltheblocks_blockchain, address, page_num, page_size):
    url = f"https://api.alltheblocks.net/{alltheblocks_blockchain}/coin/address/{address}"
    if page_num:
        url += f"?pageNumber={page_num}"
    if page_size:
        url += f"&pageSize={page_size}"
    response = json.loads(requests.get(url).content)
    #app.logger.info(response)
    return [ response['number'], response['size'], response['totalPages'], response['content'] ]

def request_cold_wallet_transactions(blockchain, alltheblocks_blockchain, address, debug=False):
    farmed_balance = 0
    records = []
    app.logger.info("Requesting {0} wallet transactions for {1}".format(alltheblocks_blockchain, address))
    page_num = None
    page_size = None
    while True:
        [page_num, page_size, total_pages, transactions] = request_cold_wallet_transactions_page(alltheblocks_blockchain, address, page_num, page_size)
        records.extend(transactions)
        if page_num >= total_pages:
            break  # have all the pages of response
        else: # get the next page
            page_num += 1
    app.logger.info("Found {0} transactions for {1}: {2}.".format(len(records), blockchain, address))
    for rec in records:
        if rec['coinType'] == 'FARMER_REWARD':
            farmed_balance += int(rec['amount']) / MOJO_PER_COIN[blockchain]
    save_cold_wallet_transactions(blockchain, address, records)
    app.logger.info("Received cold wallet farmed balance of {0}".format(farmed_balance))
    return farmed_balance

def request_cold_wallet_balance(blockchain, cold_wallet_cache, alltheblocks_blockchain, address, debug=False):
    total_balance = 0.0
    farmed_balance = 0.0
    if address in cold_wallet_cache: # First initialize to the last good values received.
        if 'total_balance' in cold_wallet_cache[address]:
            total_balance = cold_wallet_cache[address]['total_balance']
        if 'farmed_balance' in cold_wallet_cache[address]:
            farmed_balance = cold_wallet_cache[address]['farmed_balance']
    app.logger.info("Requesting {0} wallet balance for {1}".format(alltheblocks_blockchain, address))
    url = f"https://api.alltheblocks.net/{alltheblocks_blockchain}/address/{address}"
    try:
        if debug:
            http.client.HTTPConnection.debuglevel = 1
        response = json.loads(requests.get(url).content)
        total_balance = response['balance'] / MOJO_PER_COIN[blockchain]
        app.logger.info("Received cold wallet total balance of {0}".format(total_balance))
        # Only cache a valid response, if service is unreachable don't save anything
        if total_balance:
            farmed_balance = request_cold_wallet_transactions(blockchain, alltheblocks_blockchain, address, debug)
            if farmed_balance:
                # Store summary results for this cold wallet address
                cold_wallet_cache[address] = {
                    'total_balance': total_balance,
                    'farmed_balance': farmed_balance
                }
    except Exception as ex:
        app.logger.error("Failed to request {0} due to {1}".format(url, str(ex)))
        traceback.print_exc()
    finally:
        http.client.HTTPConnection.debuglevel = 0
    return total_balance  # May be None if no good response received

last_cold_wallet_request_time = None
def cold_wallet_balance(blockchain):
    global last_cold_wallet_request_time
    total_balance = 0.0
    alltheblocks_blockchain = globals.get_alltheblocks_name(blockchain)
    addresses_per_blockchain = load_cold_wallet_addresses()
    cold_wallet_cache = load_cold_wallet_cache()
    if blockchain in addresses_per_blockchain:
        if not last_cold_wallet_request_time or last_cold_wallet_request_time <= \
                (datetime.datetime.now() - datetime.timedelta(minutes=ALLTHEBLOCKS_REQUEST_INTERVAL_MINS)):
            for address in addresses_per_blockchain[blockchain]:
                address_balance = request_cold_wallet_balance(blockchain, cold_wallet_cache, alltheblocks_blockchain, address)
                if address_balance:
                    total_balance += address_balance
                else:
                    app.logger.error("No cold wallet details found for {0} {1}.".format(blockchain, address))
            save_cold_wallet_cache(cold_wallet_cache)
            last_cold_wallet_request_time = datetime.datetime.now()
            return total_balance
        else:
            for address in addresses_per_blockchain[blockchain]:
                if address in cold_wallet_cache:
                    app.logger.debug(cold_wallet_cache[address])
                    cached_cold_balance = float(cold_wallet_cache[address]['total_balance'])
                    total_balance += cached_cold_balance
            return total_balance
    return 0.0 # No cold wallet addresses to check, so no errors obviously

def load_cold_wallet_transactions(blockchain, address):
    data = {}
    cache_file =  COLD_WALLET_CACHE_DIR + '/' + blockchain + '/' + address + ".json"
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r') as f:
                data = json.load(f)
        except Exception as ex:
            msg = "Unable to read cold wallet transactions from {0} because {1}".format(cache_file, str(ex))
            app.logger.error(msg)
    return data

def cold_wallet_farmed_balance(blockchain):
    farmed_balance = 0
    addresses_per_blockchain = load_cold_wallet_addresses()
    cold_wallet_cache = load_cold_wallet_cache()
    if blockchain in addresses_per_blockchain:
        for address in addresses_per_blockchain[blockchain]:
            if address in cold_wallet_cache:
                farmed_balance += float(cold_wallet_cache[address]['farmed_balance'])
        return farmed_balance
    return 0.0 # No cold wallet addresses to check

# Only for Chia on the controller for now.
def cold_wallet_farmed_most_recent_date(blockchain):
    if blockchain != 'chia':
        raise Exception("Most recent cold wallet farmed block lookup not supported off controller.")
    most_recent_farmed_block_time = 0 # Seconds since epoch
    addresses_per_blockchain = load_cold_wallet_addresses()
    if blockchain in addresses_per_blockchain:
        for address in addresses_per_blockchain[blockchain]:
            transactions = load_cold_wallet_transactions(blockchain, address)
            for transaction in transactions:
                if transaction['coinType'] == 'FARMER_REWARD':
                    if most_recent_farmed_block_time < transaction['timestamp']:
                        most_recent_farmed_block_time = transaction['timestamp']
    return most_recent_farmed_block_time

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
                        app.logger.error("Failed to parse a decimal number from {0}".format(price_value[1:].strip()))
                else:
                    app.logger.info("No price found for blockchain: {0}".format(blockchain))
                    pass
    return prices

# NOT USED: ATB api does not provide prices as of 2022-03-12, every price shows as "-1.0"
def request_prices_api(prices, debug=False):
    url = "https://api.alltheblocks.net/atb/blockchain/settings-and-stats"
    app.logger.info("Requesting recent pricing for blockchains from {0}".format(url))
    if debug:
        http.client.HTTPConnection.debuglevel = 1
    data = json.loads(requests.get(url).content)
    http.client.HTTPConnection.debuglevel = 0
    for coin in data:
        app.logger.info("{0} @ {1}".format(coin['displayName'].lower(),coin['stats']['priceUsd']))
        try:
            if coin['stats']['priceUsd'] > 0:  # -1 means no exchange value found
                prices[coin['displayName'].lower()] = coin['stats']['priceUsd']
        except Exception as ex:
            traceback.print_exc()
    return prices

last_price_request_time = None
def get_prices():
    global last_price_request_time
    prices = load_prices_cache()
    if not last_price_request_time or last_price_request_time <= \
            (datetime.datetime.now() - datetime.timedelta(minutes=ALLTHEBLOCKS_REQUEST_INTERVAL_MINS)):
            try:
                request_prices(prices)
            except:
                traceback.print_exc()
            last_price_request_time = datetime.datetime.now()
    save_prices_cache(prices)
    try:
        save_exchange_rates()
    except: 
        traceback.print_exc()
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
