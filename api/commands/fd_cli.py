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

# No need to reward recover for either Chia or Chives
def get_full_node_rpc_port(blockchain):
    if blockchain == 'btcgreen':
        return 18942
    if blockchain == 'cactus':
        return 11555
    if blockchain == 'cryptodoge':
        return 16795
    if blockchain == 'flax':
        return 6755
    if blockchain == 'flora':
        return 18755
    if blockchain == 'hddcoin':
        return 28555
    if blockchain == 'maize':
        return 8755
    if blockchain == 'nchain':
        return 38555
    if blockchain == 'staicoin':
        return 1758
    if blockchain == 'stor':
        return 8155
    raise Exception(f"Unknown rpc_port for blockchain: {blockchain}")

def reward_recovery(wallet_id, launcher_id, pool_contract_address):
    app.logger.info("NFT reward recovery requested for {wallet_id} {launcher_id} {pool_contract_address}")
    logfile = "/root/.chia/machinaris/logs/fd-cli.log"
    log_fd = os.open(logfile, os.O_RDWR | os.O_CREAT)
    log_fo = os.fdopen(log_fd, "a+")
    vars = {}
    blockchain = globals.enabled_blockchains()[0]
    network_path = globals.get_blockchain_network_path(blockchain)
    network_name = globals.get_blockchain_network_name(blockchain)
    vars['FD_CLI_BC_DB_PATH'] = f'{network_path}/db/blockchain_v1_{network_name}.sqlite'
    vars['FD_CLI_WT_DB_PATH'] = f'{network_path}/wallet/db/blockchain_wallet_v1_{network_name}_{wallet_id}.sqlite'
    fd_env = os.environ.copy()
    fd_env.update(vars)
    rpc_port = get_full_node_rpc_port(blockchain)
    cmd = f"/usr/local/bin/fd-cli nft-recover -l {launcher_id} -p {pool_contract_address} -nh 127.0.0.1 -np {rpc_port} -ct {network_path}/config/ssl/full_node/private_full_node.crt -ck {network_path}/config/ssl/full_node/private_full_node.key"
    app.logger.info(f"Executing NFT 1/8 win recovery for {blockchain}: {cmd}")
    log_fo.write("\n\nExecuted at: {0}\n{1}".format(time.strftime("%Y%m%d-%H%M%S"), cmd))
    log_fo.flush()
    proc = Popen(cmd,cwd="/fd-cli", env=fd_env, shell=True, universal_newlines=True, stdout=log_fo, stderr=log_fo)
    try:
        outs, errs = proc.communicate(timeout=1800)
    except TimeoutExpired:
        proc.kill()
        proc.communicate()
    if errs:
        app.logger.error(errs.decode('utf-8'))
    elif outs:
        app.logger.info(outs.decode('utf-8'))
    else:
        app.logger.error("Nothing returned from fd-cli call.")
