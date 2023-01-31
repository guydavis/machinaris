#
# Calculates effort per blockchain - by definition this is an estimate!
#


import datetime
import http
import json
import os
import re
import requests
import socket
import sqlite3
import time
import traceback

from flask import g

from common.config import globals
from common.utils import converters
from api.commands import chia_cli, websvcs, rpc
from api import app, utils

# 
# Calculates current effort on this blockchain which is time since last farmed block (or oldest plot if no blocks farmed)
# divided by the _current_ ETW (estimated time to win).
#
# This is not a perfect calculation but rather an ESTIMATE!  In particular, weird farms will report strange effort values.
# For example, consider a farm that is one year old which had a single plot for 11 months, then in the last few days shot up 
# to 1000 plots. If it hasn't farmed a block yet, we have 1 year of farming over a current ETW of just a 1 month 
# so "Current Effort" is a huge 1200%. This is an edge case however.  Most farms where total plots size and blockchain 
# netspace isn't dramatically changing will have a "reasonable" effort value.
#

oldest_plot_check_time = None
oldest_plot_file_time = None
def get_oldest_plot_file_time():
    global oldest_plot_check_time, oldest_plot_file_time
    if not oldest_plot_check_time or oldest_plot_check_time <= (datetime.datetime.now() - datetime.timedelta(days=1)):
        oldest_plot_check_time = datetime.datetime.now()
        for plot_dir in globals.get_disks("plots"):
            plots = [f for f in os.listdir(plot_dir) if os.path.isfile(os.path.join(plot_dir,f))]
            for plot in plots:
                match = re.match("plot(?:-mmx)?-k(\d+)(?:-c\d)?-(\d+)-(\d+)-(\d+)-(\d+)-(\d+)-(\w+).plot", plot)
                if match:
                    created_at_str = "{0}-{1}-{2} {3}:{4}".format( match.group(2),match.group(3),match.group(4),match.group(5),match.group(6))
                    created_at_secs = time.mktime(datetime.datetime.strptime(created_at_str, "%Y-%m-%d %H:%M").timetuple())
                    if not oldest_plot_file_time or oldest_plot_file_time > created_at_secs:
                        #app.logger.info("Found oldest plot so far at: {0}".format(created_at_str))
                        oldest_plot_file_time = created_at_secs # Oldest plot date so far
    return oldest_plot_file_time 

def collect():
    with app.app_context():
        blockchain_rpc = rpc.RPC()
        current_datetime = datetime.datetime.now().strftime("%Y%m%d%H%M")
        blockchain = globals.enabled_blockchains()[0]
        try:
            if blockchain == 'mmx':
                app.logger.debug("Unable to calculate effort for MMX blockchain.  Only Chia and forks supported.")
                return
            farm_summary = chia_cli.load_farm_summary(blockchain)
            wallets = blockchain_rpc.get_wallets()
            if len(wallets) < 1:  # If no wallet status returned, then no effort stat to record.
                return
            transactions = blockchain_rpc.get_transactions(wallets[0]['id'], reverse=True) # Search primary wallet only
            most_recent_block_reward_time = None
            for transaction in transactions:  # Order is reversed; newest to oldest
                #app.logger.info("At {0}, {1} type had amount: {2}".format(readable(transaction.created_at_time), transaction.type, transaction.additions[0].amount))
                if transaction.type == 3: # FEE_REWARD type
                    app.logger.info("At {0}, recent hot wallet fee reward was found.".format(readable(transaction.created_at_time)))
                    most_recent_block_reward_time = transaction.created_at_time
                    break
            # For Chia only (on the controller), check for a more recently farmed block time in cold wallet transactions
            if blockchain == 'chia':
                most_recent_block_reward_time_cold_wallet =  websvcs.cold_wallet_farmed_most_recent_date(blockchain) # Order is reversed; newest to oldest
                if most_recent_block_reward_time < most_recent_block_reward_time_cold_wallet:
                    app.logger.info("At {0}, a more recent cold wallet fee reward was found.".format(readable(most_recent_block_reward_time_cold_wallet)))
                    most_recent_block_reward_time = most_recent_block_reward_time_cold_wallet
            etw_minutes = converters.etw_to_minutes(farm_summary.time_to_win)
            if most_recent_block_reward_time:  # Calculate since most recent farmed block
                effort = (time.time() - most_recent_block_reward_time) / 60 / etw_minutes * 100
                app.logger.info("Effort based on most recently farmed block ({0}) is {1}%.".format(readable(most_recent_block_reward_time), round(effort, 0)))
                send_stat(blockchain, effort, current_datetime)
            elif etw_minutes > 0:  # No blocks farmed, so calculate since oldest plot file creation (aka farm duration)
                oldest_plot_time = get_oldest_plot_file_time()
                effort = (time.time() - oldest_plot_time) / 60 / etw_minutes * 100
                app.logger.info("Effort based on oldest plot file ({0}) is {1}%".format(readable(oldest_plot_time)), round(effort, 0))
                send_stat(blockchain, effort, current_datetime)
        except:
            app.logger.info("Failed to calculate blockchain effort.")
            app.logger.info(traceback.format_exc())

def readable(seconds):
    return time.strftime('%Y-%m-%d %H:%M', time.localtime(seconds))

def send_stat(blockchain, value, current_datetime):
    try:
        payload = []
        payload.append({
            "hostname": utils.get_hostname(),
            "blockchain": blockchain,
            "value": value,
            "created_at": current_datetime,
        })
        utils.send_post('/stats/effort', payload, debug=False)
    except:
        app.logger.info("Failed to send latest stat to /stats/effort.")
        app.logger.info(traceback.format_exc())
