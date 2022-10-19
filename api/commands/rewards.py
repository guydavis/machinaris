#
# Performs a daily NFT wins recovery using either:
#    plotnft claim {wallet_id_num} - builtin from Chia CLI  OR
#    fd-cli: https://github.com/Flora-Network/flora-dev-cli
#   

import datetime
import json
import os
import sqlite3
import time
import traceback

from subprocess import Popen, TimeoutExpired, PIPE

from common.config import globals
from common.models import wallets as w
from api import app

CHIA_PLOTNFT_INFO_FILE = '/root/.chia/machinaris/config/chia_plotnfts.json'
QUALIFIED_COINS_CACHE_FILE = '/root/.chia/machinaris/cache/reward_coins.json'
BLOCKCHAINS_WITH_PLOTNFT_CLAIM_CMD = ['chia']

def reward_recovery(wallet_id, launcher_id, pool_contract_address):
    with app.app_context():
        from api import db
        blockchain = globals.enabled_blockchains()[0]
        app.logger.info(f"On {blockchain}, NFT reward recovery requested for wallet {wallet_id} {launcher_id} {pool_contract_address}")
        if blockchain in BLOCKCHAINS_WITH_PLOTNFT_CLAIM_CMD:
            for wallet in db.session.query(w.Wallet).filter(w.Wallet.blockchain==blockchain).order_by(w.Wallet.blockchain).all():
                for wallet_num in wallet.wallet_nums():
                    execute_plotnft_claim_recovery(wallet_num)
        else: # Try old FD-CLI recovery instead
            execute_fd_cli_recovery(wallet_id, launcher_id, pool_contract_address)

def execute_plotnft_claim_recovery(wallet_num):
    blockchain = globals.enabled_blockchains()[0]
    blockchain_binary = globals.get_blockchain_binary(blockchain)
    cmd = "{0} plotnft claim -i {1}".format(blockchain_binary, wallet_num)
    app.logger.info(f"Claiming NFT reward recovery for {blockchain}: {cmd}")
    logfile = "/root/.chia/machinaris/logs/rewards.log"
    log_fd = os.open(logfile, os.O_RDWR | os.O_CREAT)
    log_fo = os.fdopen(log_fd, "a+")
    log_fo.write("\n\nExecuted at: {0}\n{1}\n".format(time.strftime("%Y-%m-%d-%H:%M:%S"), cmd))
    log_fo.flush()
    proc = Popen(cmd, cwd="/", shell=True, universal_newlines=True, stdout=log_fo, stderr=log_fo)
    try:
        outs, errs = proc.communicate(timeout=1800)
        if errs:
            app.logger.error(errs.decode('utf-8'))
        elif outs:
            app.logger.info(outs.decode('utf-8'))
    except TimeoutExpired:
        proc.kill()
        proc.communicate()
        app.logger.error("Timeout expired for plotnft claim call.")

def execute_fd_cli_recovery(wallet_id, launcher_id, pool_contract_address):
    app.logger.info("NFT reward recovery requested for {wallet_id} {launcher_id} {pool_contract_address}")
    blockchain = globals.enabled_blockchains()[0]
    rpc_port = globals.get_full_node_rpc_port(blockchain)
    if not rpc_port:
        app.logger.info("Skipping NFT reward recovery on unsupported blockchain: {0}".format(blockchain))
        return
    logfile = "/root/.chia/machinaris/logs/rewards.log"
    log_fd = os.open(logfile, os.O_RDWR | os.O_CREAT)
    log_fo = os.fdopen(log_fd, "a+")
    vars = {}
    network_path = globals.get_blockchain_network_path(blockchain)
    network_name = globals.get_blockchain_network_name(blockchain)
    blockchain_db_path = f'{network_path}/db/blockchain_v2_{network_name}.sqlite'
    if os.path.exists(blockchain_db_path):  # First check for a v2 blockchain and wallet
        vars['FD_CLI_BC_DB_PATH'] = blockchain_db_path
        wallet_db_path = f'{network_path}/wallet/db/blockchain_wallet_v2_r1_{network_name}_{wallet_id}.sqlite'
        if os.path.exists(wallet_db_path):
            vars['FD_CLI_WT_DB_PATH'] = wallet_db_path
        else:
            app.logger.error("Reward Recovery found no v2 wallet database: {0}".format(wallet_db_path))
    else: # Then check for old v1 blockchain and wallet if no v2 found
        blockchain_db_path = f'{network_path}/db/blockchain_v1_{network_name}.sqlite'
        if os.path.exists(blockchain_db_path):  # Then check for a v1 blockchain and wallet
            vars['FD_CLI_BC_DB_PATH'] = blockchain_db_path
            wallet_db_path = f'{network_path}/wallet/db/blockchain_wallet_v1_{network_name}_{wallet_id}.sqlite'
            if os.path.exists(wallet_db_path):
                vars['FD_CLI_WT_DB_PATH'] = wallet_db_path
            else:
                app.logger.error("Reward Recovery found no v1 wallet database: {0}".format(wallet_db_path))
        else:
            app.logger.error("Reward Recovery found neither v1 or v2 blockchain database at: {0}/db".format(network_path))
    fd_env = os.environ.copy()
    fd_env.update(vars)
    cmd = f"/usr/local/bin/fd-cli nft-recover -l {launcher_id} -p {pool_contract_address} -nh 127.0.0.1 -np {rpc_port} -ct {network_path}/config/ssl/full_node/private_full_node.crt -ck {network_path}/config/ssl/full_node/private_full_node.key"
    app.logger.info(f"Executing NFT 7/8 win recovery for {blockchain}: {cmd}")
    log_fo.write("\n\nExecuted at: {0}\nFD_CLI_BC_DB_PATH={1} FD_CLI_WT_DB_PATH={2} {3}\n".format(
        time.strftime("%Y-%m-%d-%H:%M:%S"), vars['FD_CLI_BC_DB_PATH'], vars['FD_CLI_WT_DB_PATH'], cmd))
    log_fo.flush()
    proc = Popen(cmd,cwd="/flora-dev-cli", env=fd_env, shell=True, universal_newlines=True, stdout=log_fo, stderr=log_fo)
    try:
        outs, errs = proc.communicate(timeout=1800)
        if errs:
            app.logger.error(errs.decode('utf-8'))
        elif outs:
            app.logger.info(outs.decode('utf-8'))
        else:
            app.logger.error("Nothing returned from fd-cli call.")
    except TimeoutExpired:
        proc.kill()
        proc.communicate()
        app.logger.error("Timeout expired for fd-cli call.")

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
    query = f"SELECT coin_name, coin_parent, amount FROM coin_record WHERE {spent_column_name} == 0 AND timestamp {qualified_op} (strftime('%s', 'now') - 604800) AND puzzle_hash LIKE ? ORDER BY timestamp DESC"
    app.logger.debug(query)
    cursor.execute(query, (bytes.fromhex(puzzle_hash),))
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
