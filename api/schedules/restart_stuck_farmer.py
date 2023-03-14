#
# On a farmer, records the current peak height of the blockchain every X minutes.
# Restarts the farming services if the peak height has not increased in that time.
# Gunicorn currently schedules this check for once every 5 minutes.
#
# Also, if a limit is optionally set, will trigger a blockchain restart if exceeds
# X GB over a period of time.  Useful for old forks which are memory leakers per day.
# 

import datetime as dt
import math
import os
import subprocess

from api import app
from common.config import globals
from api.commands import chia_cli, plotman_cli

RESTART_IF_STUCK_MINUTES = 15

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
            max_allowed_container_memory_gib = float(app.config['RESTART_FARMER_IF_CONTAINER_MEMORY_EXCEEDS_GIB'])
            if max_allowed_container_memory_gib <= 0: # Check is disabled if negative default
                memory_exceeded_since = None
                return
            container_memory_gib = globals.get_container_memory_usage_bytes() / 1024 / 1024 / 1024
            app.logger.info("Would RESTART bloated farmer if current {:.2f} GiB usage is more than {:.2f} GiB limit.".format(container_memory_gib, max_allowed_container_memory_gib))
            plotting_jobs = plotman_cli.load_plotting_summary()
            if not plotting_jobs or len(plotting_jobs.rows) > 0:
                memory_exceeded_since = None
                return
            if container_memory_gib > 0 and max_allowed_container_memory_gib < container_memory_gib:
                if not memory_exceeded_since:
                    memory_exceeded_since = dt.datetime.now()
                minutes_diff = math.ceil((dt.datetime.now() - memory_exceeded_since).total_seconds() / 60.0)
                if minutes_diff >= RESTART_IF_STUCK_MINUTES:
                    app.logger.info("***************** RESTARTING BLOATED FARMER AT {:.2f} GiB!!! ******************".format(container_memory_gib))
                    chia_cli.restart_farmer(blockchain)
                    return
            else:
                memory_exceeded_since = None # Not over the limit anymore
        except Exception as ex:
            app.logger.info("Skipping bloated farmer check due to exception: {0}".format(str(ex)))