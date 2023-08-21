#
# Performs a REST call to controller (possibly localhost) of latest pools status.
#

import asyncio
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
from common.models import pools as p
from api.commands import pools_cli, rpc
from api import app
from api import utils

def update():
    with app.app_context():
        blockchain_rpc = rpc.RPC()
        try:
            for blockchain in globals.enabled_blockchains():
                if not blockchain in p.POOLABLE_BLOCKCHAINS:
                    continue
                payload = []
                hostname = utils.get_hostname()
                pools =  blockchain_rpc.get_pool_states(blockchain)
                for pool in pools:
                    app.logger.debug(pool)
                    launcher_id = pool['pool_config']['launcher_id']
                    login_link = ""  # Only request login link if a pool_url is found (not self-farming)
                    if 'pool_url' in pool['pool_config'] and pool['pool_config']['pool_url']:
                        login_link = pools_cli.get_pool_login_link(launcher_id)
                    if launcher_id.startswith('0x'):
                        launcher_id = launcher_id[2:]
                    payload.append({
                        "unique_id": hostname + '_' + blockchain + '_' + launcher_id,
                        "hostname": hostname,
                        "blockchain": blockchain,
                        "launcher_id": launcher_id,
                        "login_link": login_link,
                        "pool_state": json.dumps(pool),
                        "updated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
                #app.logger.info(payload)
                response = utils.send_post('/pools/', payload, debug=False)
                #app.logger.info(response.content)
        except Exception as ex:
            app.logger.info("Failed to load and send pools status because {0}".format(str(ex)))
