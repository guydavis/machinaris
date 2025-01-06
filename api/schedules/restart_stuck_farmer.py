#
# On a farmer, records the current peak height of the blockchain every X minutes.
# Restarts the farming services if the peak height has not increased in that time.
# Gunicorn currently schedules this check for once every 5 minutes.
#
# Also, if a limit is optionally set, will trigger a blockchain restart if exceeds
# X GB over a period of time.  Useful for old forks which are memory leakers per day.
#
# Also, if no partial proofs for pools for a while, restart farmer.
#

import datetime as dt
import math
import os
import subprocess
import traceback

from web import db
from api import app
from common.config import globals
from api.commands import chia_cli, plotman_cli
from common.models import partials as pr
from common.models import plotnfts as pn

RESTART_IF_STUCK_MINUTES = 15
RESTART_IF_STUCK_NO_PARTIALS_MINUTES = 60

last_peak = None
last_peak_time = None
def stale_peak(blockchain_show):
    global last_peak, last_peak_time
    current_stale_peak = None
    for line in blockchain_show:
        if line.startswith('Current Blockchain Status'):
            if 'Not Synced. Peak height: ' in line:
                current_stale_peak = line.split(':')[2].strip() # End of line after 2nd colon
    if current_stale_peak:
        if last_peak and last_peak_time:
            minutes_diff = math.ceil((dt.datetime.now() - last_peak_time).total_seconds() / 60.0)
            if last_peak == current_stale_peak:
                if minutes_diff >= RESTART_IF_STUCK_MINUTES:
                    app.logger.info("Executing unsynced blockchain restart due to stuck peak height of {0} for {1} minutes.".format(current_stale_peak, minutes_diff))
                    last_peak = None
                    last_peak_time = None
                    return True  # Request the restart
                else:
                    app.logger.info("Monitoring unsynced blockchain stuck on peak height of {0} since {1}.".format(current_stale_peak, last_peak_time.strftime("%Y-%m-%d-%H:%M:%S")))
        else: # First time recording stale peak, just monitor for next time
            last_peak = current_stale_peak
            last_peak_time = dt.datetime.now()
            app.logger.info("Recording first stale peak of {0} at {1}.".format(last_peak, last_peak_time.strftime("%Y-%m-%d-%H:%M:%S")))
    return False # Not stuck on a stale peak so DO NOT restart

memory_exceeded_since = None
def execute():
    global memory_exceeded_since
    blockchain = globals.enabled_blockchains()[0]
    if blockchain == 'mmx':
        return # Chia+forks only right now
    with app.app_context():
        # First check if blockchain is stuck (not progressing) and needs a kick to get it moving...
        try:
            if stale_peak(chia_cli.load_blockchain_show(blockchain).text.replace('\r', '').split('\n')):
                app.logger.info("***************** RESTARTING STUCK FARMER!!! ******************")
                chia_cli.restart_farmer(blockchain)
                return
        except Exception as ex:
            app.logger.info("Skipping stuck farmer check due to exception: {0}".format(str(ex)))
        # If NOT plotting (which uses lots of memory), restart a bloated farmer if exceeds an optional limit of X GiB over Y minutes
        try:
            max_allowed_container_memory_gb = float(app.config['RESTART_FARMER_IF_CONTAINER_MEMORY_EXCEEDS_GB'])
            if max_allowed_container_memory_gb <= 0: # Check is disabled if negative default
                memory_exceeded_since = None
                return
            container_memory_gb = globals.get_container_memory_usage_bytes() / 1024 / 1024 / 1024
            if globals.plotting_enabled():
                plotting_jobs = plotman_cli.load_plotting_summary()
                if not plotting_jobs or len(plotting_jobs.rows) > 0:
                    memory_exceeded_since = None
                    return
            if container_memory_gb > 0 and max_allowed_container_memory_gb < container_memory_gb:
                if not memory_exceeded_since:
                    memory_exceeded_since = dt.datetime.now()
                minutes_diff = math.ceil((dt.datetime.now() - memory_exceeded_since).total_seconds() / 60.0)
                if minutes_diff >= RESTART_IF_STUCK_MINUTES:
                    if not globals.wallet_running():  # Only if wallet is not currently being synced
                        app.logger.info("***************** RESTARTING BLOATED FARMER AT {:.2f} GiB!!! Exceeded {:.2f} GiB limit. ******************".format(container_memory_gb, max_allowed_container_memory_gb))
                        chia_cli.restart_farmer(blockchain)
                        memory_exceeded_since = None
                        return
                    else:
                        app.logger.info("Would RESTART bloated farmer as current {:.2f} GiB usage exceeds the {:.2f} GiB limit, but wallet is currently running.".format(container_memory_gb, max_allowed_container_memory_gb))
                else:
                    app.logger.info("Would RESTART bloated farmer as current {:.2f} GiB usage exceeds the {:.2f} GiB limit".format(container_memory_gb, max_allowed_container_memory_gb) + ", however only {0} minutes elapsed.".format(minutes_diff))
            else:
                memory_exceeded_since = None # Not over the limit anymore
        except Exception as ex:
            app.logger.info("Skipping bloated farmer check due to exception: {0}".format(str(ex)))
            traceback.print_exc()
        # If no partial proofs for pools for a while, restart farmer
        try:
            if not globals.wallet_running():  # Only if wallet is not currently being synced
                plotnfts = db.session.query(pn.Plotnft).filter(pn.Plotnft.blockchain == blockchain).all()
                is_pooling = False
                for plotnft in plotnfts:
                    if not "SELF_POOLING" in plotnft.details:
                        is_pooling = True
                if not is_pooling:
                    return # No plotnft currently pooling (not self-pooling), so don't expect any partials
                partials = db.session.query(pr.Partial).filter(pr.Partial.blockchain == blockchain, pr.Partial.created_at >= (dt.datetime.now() - dt.timedelta(minutes=RESTART_IF_STUCK_NO_PARTIALS_MINUTES))).all()
                if len(partials) == 0:
                    app.logger.info("***************** RESTARTING FARMER DUE TO NO PARTIALS FOR {} MINUTES!!! ******************".format(RESTART_IF_STUCK_MINUTES))
                    chia_cli.restart_farmer(blockchain)
                    return
        except Exception as ex:
            app.logger.info("Skipping stuck farmer check due to exception: {0}".format(str(ex)))
