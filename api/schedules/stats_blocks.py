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

def collect():
    with app.app_context():
        gc = globals.load()
        if not gc['farming_enabled']:
            app.logger.info(
                "Skipping block win stats collection as not farming on this Machinaris instance.")
            return
        #app.logger.info("Collecting stats about won blocks.")
        blockchain = globals.enabled_blockchains()[0]
        blocks = log_parser.recent_farmed_blocks(blockchain)
        store_locally(blockchain, blocks)
        if not gc['is_controller']:
            send_to_controller(blockchain, blocks)

def store_locally(blockchain, blocks):
    hostname = utils.get_hostname()
    for block in blocks.rows:
        try:
            if not db.session.query(stats.StatFarmedBlocks).filter(stats.StatFarmedBlocks.blockchain==blockchain,stats.StatFarmedBlocks.farmed_block==block['farmed_block']).first():
                db.session.add(stats.StatFarmedBlocks(hostname=hostname, 
                    blockchain=blockchain, 
                    challenge_id=block['challenge_id'], 
                    plot_files=block['plot_files'], 
                    proofs_found=block['proofs_found'], 
                    time_taken=block['time_taken'], 
                    farmed_block=block['farmed_block'], 
                    created_at=block['created_at']))
            else:
                app.logger.debug("Already in database: {0}".format(block['farmed_block']))
        except:
            app.logger.info(traceback.format_exc())
    db.session.commit()

def send_to_controller(blockchain, blocks):
    try:
        payload = []
        for block in blocks.rows:
            payload.append(
                {
                    "hostname": utils.get_hostname(),
                    "blockchain": blockchain, 
                    "challenge_id": block['challenge_id'], 
                    "plot_files": block['plot_files'], 
                    "proofs_found": int(block['proofs_found']), 
                    "time_taken": block['time_taken'], 
                    "farmed_block": block['farmed_block'], 
                    "created_at": block['created_at'],
                }
            )
        utils.send_post('/stats/farmedblocks/', payload, debug=False)
    except:
        app.logger.info("Failed to send latest stat to {0}.".format('/stats/farmedblocks'))
        app.logger.info(traceback.format_exc())
