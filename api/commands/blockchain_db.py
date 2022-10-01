#
# DB access to blockchain databases, used when RPC API isn't enough
#

import os
import sqlite3

# TODO Handle other blockchains
if "chia" == globals.enabled_blockchains()[0]:
    # https://github.com/Chia-Network/chia-blockchain/blob/main/chia/util/bech32m.py
    from chia.util.bech32m import decode_puzzle_hash

from common.config import globals
from api import app

def _get_blockchain_db_path():
    blockchain = globals.enabled_blockchains()[0]
    network_path = globals.get_blockchain_network_path(blockchain)
    network_name = globals.get_blockchain_network_name(blockchain)
    blockchain_db_path = f'{network_path}/db/blockchain_v2_{network_name}.sqlite'
    if os.path.exists(blockchain_db_path):  # First check for a v2 blockchain
        app.logger.info("For {0}, found v2 blockchain database at: {1}".formtat(blockchain, blockchain_db_path))
        return blockchain_db_path
    else: # Then check for old v1 blockchain and wallet if no v2 found
        blockchain_db_path = f'{network_path}/db/blockchain_v1_{network_name}.sqlite'
        if os.path.exists(blockchain_db_path):  # Then check for a v1 blockchain
            app.logger.info("For {0}, found v1 blockchain database at: {1}".formtat(blockchain, blockchain_db_path))
            return blockchain_db_path
    raise Exception("Found neither v1 or v2 blockchain database at: {0}/db".format(network_path))

def get_unspent_coins(pool_contract_address):
    puzzle_hash = decode_puzzle_hash(pool_contract_address)
    db_path = _get_blockchain_db_path()
    spent_column_name = 'spent' # v1
    if '_v2_' in db_path:
        spent_column_name = 'spent_index'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        f"SELECT * "
        f"FROM coin_record "
        f"WHERE {spent_column_name} == 0 "
        f"AND timestamp <= (strftime('%s', 'now') - 604800) "
        f"AND puzzle_hash LIKE '{puzzle_hash}' "
        f"ORDER BY timestamp DESC")
    rows = []
    for row in cursor.fetchall():
        amount = int.from_bytes(row[7], byteorder='big', signed=False)
        if amount > 0:
            rows.append(row)
    if len(rows) == 0:
        app.logger.info("No coins are eligible for recovery yet. Notice that 604800 seconds must pass since coin creation to recover it.")
    return rows