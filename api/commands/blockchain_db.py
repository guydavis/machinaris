#
# DB access to blockchain databases, used when RPC API isn't enough
#

import json
import os
import sqlite3

from common.config import globals
from api import app

CHIA_PLOTNFT_INFO_FILE = '/root/.chia/machinaris/config/chia_plotnfts.json'
QUALIFIED_COINS_CACHE_FILE = '/root/.chia/machinaris/cache/reward_coins.json'

def _get_blockchain_db_path():
    blockchain = globals.enabled_blockchains()[0]
    network_path = globals.get_blockchain_network_path(blockchain)
    network_name = globals.get_blockchain_network_name(blockchain)
    blockchain_db_path = f'{network_path}/db/blockchain_v2_{network_name}.sqlite'
    if os.path.exists(blockchain_db_path):  # First check for a v2 blockchain
        app.logger.info("For {0}, found v2 blockchain database at: {1}".format(blockchain, blockchain_db_path))
        return blockchain_db_path
    else: # Then check for old v1 blockchain and wallet if no v2 found
        blockchain_db_path = f'{network_path}/db/blockchain_v1_{network_name}.sqlite'
        if os.path.exists(blockchain_db_path):  # Then check for a v1 blockchain
            app.logger.info("For {0}, found v1 blockchain database at: {1}".format(blockchain, blockchain_db_path))
            return blockchain_db_path
    raise Exception("Found neither v1 or v2 blockchain database at: {0}/db".format(network_path))

def get_unspent_coins(puzzle_hash, qualified=True):
    db_path = _get_blockchain_db_path()
    spent_column_name = 'spent' # v1
    if '_v2_' in db_path:
        spent_column_name = 'spent_index'
    if qualified: # older than 1 week
        qualified_op = '<='
    else: # newer than one week, can't be recovered yet
        qualified_op = '>'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    app.logger.info("Starting to query for unspent coins...")
    query = f"SELECT coin_name, coin_parent, amount FROM coin_record WHERE {spent_column_name} == 0 AND timestamp {qualified_op} (strftime('%s', 'now') - 604800) AND puzzle_hash == '{puzzle_hash}' ORDER BY timestamp DESC"
    app.logger.info(query)
    cursor.execute(query)
    app.logger.info("Completed query for unspent coins.")
    rows = []
    for row in cursor.fetchall():
        amount = int.from_bytes(row[7], byteorder='big', signed=False)
        if amount > 0:
            rows.append({
                'coin_name': row[0].hex(),
                'coin_parent': row[1].hex(),
                'amount': row[2]
            })
    if len(rows) == 0:
        app.logger.info("No coins are eligible for recovery yet. Note that 604800 seconds must pass since coin creation to recover it.")
    app.logger.info("Completed loop for unspent coins.")
    return rows

def save_chia_plotnfts(payload):
    try:
        with open(CHIA_PLOTNFT_INFO_FILE, 'w') as f:
            json.dump(payload, f)
    except Exception as ex:
        app.logger.error("Failed to store Chia plotnft info in {0} because {1}".format(CHIA_PLOTNFT_INFO_FILE, str(ex)))

def load_chia_plotnfts():
    data = {}
    if os.path.exists(CHIA_PLOTNFT_INFO_FILE):
        try:
            with open(CHIA_PLOTNFT_INFO_FILE) as f:
                data = json.load(f)
        except Exception as ex:
            msg = "Unable to read Chia plotnft info from {0} because {1}".format(CHIA_PLOTNFT_INFO_FILE, str(ex))
            app.logger.error(msg)
    return data

def update_qualified_coins_cache():
    coins_per_plotnft = {}
    plotnfts = load_chia_plotnfts()
    for plotnft in plotnfts:
        coins_per_plotnft[plotnft['launcher']] = get_unspent_coins(plotnft['puzzle_hash'])
    try:
        with open(QUALIFIED_COINS_CACHE_FILE, 'w') as f:
            json.dump(coins_per_plotnft, f)
    except Exception as ex:
        app.logger.error("Failed to store prices cache in {0} because {1}".format(CHIA_PLOTNFT_INFO_FILE, str(ex)))

def load_qualified_coins_cache():
    data = {}
    if os.path.exists(QUALIFIED_COINS_CACHE_FILE):
        try:
            with open(QUALIFIED_COINS_CACHE_FILE) as f:
                data = json.load(f)
        except Exception as ex:
            msg = "Unable to read qualified coins from {0} because {1}".format(QUALIFIED_COINS_CACHE_FILE, str(ex))
            app.logger.error(msg)
    return data
