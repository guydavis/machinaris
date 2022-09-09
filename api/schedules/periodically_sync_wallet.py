#
# By default, the wallet process is left running 24/7 alongside the farming process on the fullnode.
# However, the wallet chews about half the total memory and is NOT REQUIRED TO ACTUALLY FARM.
# Therefore, Machinaris users can choose leave the wallet service off, periodically running it
# up to sync, gather latest stats, then stop it again for some interval.  When rotated thru
# the full set of blockchains, this can result in a substantial memory usage decrease.
#
 
import datetime
import json
import os

from random import randrange

from api import app
from common.config import globals
from api.commands import chia_cli
from web.routes import wallet

# When this file present, we are leaving wallet paused normally, syncing every day or so
WALLET_SETTINGS_FILE = '/root/.chia/machinaris/config/wallet_settings.json'

initial_offset_delay = randrange(24)
last_wallet_start_at = None
def execute():
    global initial_offset_delay
    global last_wallet_start_at

    # On initial launch, use a random hour offset in the next 24 hours to avoid all 
    # blockchain wallets syncing at the same time, minimize concurrent memory usage.
    if initial_offset_delay > 0:
        app.logger.error("initial_offset_delay is {0}".format(initial_offset_delay))
        initial_offset_delay = initial_offset_delay - 1  # Invoked once an hour
        return

    blockchain = globals.enabled_blockchains()[0]
    if blockchain in ['mmx']:
        return  # Take no action for MMX at this point, only Chia-based blockchains
    with app.app_context():
        wallet_settings = load_wallet_settings()
        if not 'wallet_sync_frequency' in wallet_settings:
            return # Nothing to do, leave wallet running always
        wallet_sync_frequency = wallet_settings['wallet_sync_frequency']
        wallet_running = globals.wallet_running()
        if wallet_running and not last_wallet_start_at: # Start tracking now if not launched by this schedule
            last_wallet_start_at = datetime.datetime.now()
        if wallet_running and wallet_sync_frequency == 0:
            app.logger.error("SYNC: Pausing running wallet when user requested to never sync it.")
            chia_cli.pause_wallet(blockchain)  # Wallet running, user wants it to never sync
            return
        elif not wallet_running and wallet_sync_frequency == 0:
            app.logger.error("SYNC: Wallet not running as user requested no sync ever.")
            return # Nothing to do as wallet is paused and user wants it to never sync
        wallet = chia_cli.load_wallet_show(blockchain)
        if wallet_running:
            if not wallet.is_synced():
                app.logger.error("SYNC: Wallet running but still not synced. Leaving it running since {0}".format(last_wallet_start_at.strftime('%Y-%m-%d %H:%M:%S')))
            else:
                app.logger.error("SYNC: Wallet running and is now synced.  Pausing wallet now, after earlier sync start at {0}".format(last_wallet_start_at.strftime('%Y-%m-%d %H:%M:%S')))
                chia_cli.pause_wallet(blockchain)  # Wallet running, currently synced, so stop it until next sync time
        else: # Wallet not running, so check to see if a sync is due
            if last_wallet_start_at < datetime.datetime.now() - datetime.timedelta(hours=wallet_sync_frequency):
                app.logger.error("SYNC: Starting wallet sync as has not been running for {0} hours now.".format(wallet_sync_frequency))
                chia_cli.start_wallet(blockchain)  # Wallet running, user wants it to never sync
                last_wallet_start_at = datetime.datetime.now()
            else:
                app.logger.error("SYNC: NOT starting wallet sync yet as less than {0} hours since last start {0}.".format(last_wallet_start_at.strftime('%Y-%m-%d %H:%M:%S')))

def load_wallet_settings():
    data = {}
    if os.path.exists(WALLET_SETTINGS_FILE):
        try:
            with open(WALLET_SETTINGS_FILE) as f:
                data = json.load(f)
        except Exception as ex:
            msg = "Unable to read wallet settings from {0} because {1}".format(WALLET_SETTINGS_FILE, str(ex))
            app.logger.error(msg)
            return data
    return data
