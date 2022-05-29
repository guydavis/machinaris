#
# Checks for all recent farmed blocks
#

import datetime
import sqlite3
import traceback

from flask import g

from common.config import globals
from common.models import stats
from common.utils import converters
from api import app, utils, db
from api.commands import log_parser

TABLES = [ stats.StatFarmedBlocks ]

def collect():
    with app.app_context():
        gc = globals.load()
        if not gc['farming_enabled']:
            app.logger.info(
                "Skipping block win stats collection as not farming on this Machinaris instance.")
            return
        #app.logger.info("Collecting stats about won blocks.")
        current_datetime = datetime.datetime.now().strftime("%Y%m%d%H%M")
        for blockchain in globals.enabled_blockchains():
            if not blockchain == 'mmx':
                blocks = log_parser.recent_farmed_blocks(blockchain)
            store_locally(blockchain, blocks, current_datetime)
            if not gc['is_controller']:
                send_to_controller(blockchain, blocks, current_datetime)

def store_locally(blockchain, blocks, current_datetime):
    hostname = utils.get_hostname()
    for block in blocks.rows:
        try:
            db.session.add(stats.StatFarmedBlocks(hostname=hostname, 
                blockchain=blockchain, 
                challenge_id=block['challenge_id'], 
                plot_files=block['plot_files'], 
                proofs_found=block['plot_files'], 
                time_taken=block['time_taken'], 
                farmed_block=block['farmed_block'], 
                created_at=current_datetime))
        except:
            app.logger.info(traceback.format_exc())
    db.session.commit()

def send_to_controller(blockchain, blocks, current_datetime):
    try:
        payload = []
        for block in blocks.rows:
            payload.append(
                {
                    "hostname": utils.get_hostname(),
                    "blockchain": blockchain, 
                    "challenge_id": block['challenge_id'], 
                    "plot_files": block['plot_files'], 
                    "proofs_found": block['proofs_found'], 
                    "time_taken": block['time_taken'], 
                    "farmed_block": block['farmed_block'], 
                    "created_at": current_datetime,
                }
            )
        utils.send_post('/stats/farmedblocks', payload, debug=True)
    except:
        app.logger.info("Failed to send latest stat to {0}.".format('/stats/farmedblocks'))
        app.logger.info(traceback.format_exc())
