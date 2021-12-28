#
# On a farmer, records the current peak height of the blockchain every X minutes.
# Restarts the farming services if the peak height has not increased in that time.
# Gunicorn currently schedules this check for once every 5 minutes.
# 

import datetime as dt
import math
import os
import subprocess

from api import app
from common.config import globals
from api.commands import chia_cli


RESTART_IF_STUCK_MINUTES = 15
BLOCKCHAIN = os.environ['blockchains']

def restart():
    chia_binary = globals.get_blockchain_binary(BLOCKCHAIN)
    ret = subprocess.call("{0} start farmer -r >/tmp/chia_restart.log 2>&1".format(chia_binary), shell=True)
    app.logger.info("Return code from blockchain restart was {0}".format(ret))

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
                    app.logger.info("Executing unsycned blockchain restart due to stuck peak height of {0} for {1} minutes.".format(current_stale_peak, minutes_diff))
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

def execute():
    with app.app_context():
        #app.logger.info("***************** RESTART STUCK FARMER ******************")
        try:
            if stale_peak(chia_cli.load_blockchain_show(BLOCKCHAIN).text.replace('\r', '').split('\n')):
                restart()
        except Exception as ex:
            app.logger.info("Skipping stuck farmer check due to exception: {0}".format(str(ex)))
        