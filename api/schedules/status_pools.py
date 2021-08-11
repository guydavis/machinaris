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
from api.commands import chia_cli
from api.rpc import chia
from api import app
from api import utils

def update():
    if not globals.farming_enabled():
        #app.logger.info("Skipping recent pools state collection on non-farming instance.")
        return
    with app.app_context():
        try:
            blockchains = ['chia']
            # Flax doesn't support this yet.
            #if globals.flax_enabled():  
            #    blockchains.append('flax')
            for blockchain in blockchains:
                payload = []
                hostname = utils.get_hostname()
                pools =  asyncio.run(chia.get_pool_state(blockchain))
                for pool in pools:
                    launcher_id = pool['pool_config']['launcher_id']
                    login_link = chia_cli.get_pool_login_link(launcher_id)
                    app.logger.info("Pool login: {0}".format(login_link))
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
        except:
            app.logger.info("Failed to load and send pools state.")
            app.logger.info(traceback.format_exc())
