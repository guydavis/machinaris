#
# Performs a daily NFT wins recovery using fd-cli: https://github.com/Flora-Network/flora-dev-cli
#

import datetime
import os
import sqlite3
import time
import traceback

from subprocess import Popen, TimeoutExpired, PIPE

from common.config import globals
from api import app

def reward_recovery(wallet_id, launcher_id, pool_contract_address):
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

