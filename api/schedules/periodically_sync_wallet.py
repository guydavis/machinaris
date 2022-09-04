#
# By default, the wallet process is left running 24/7 alongside the farming process on the fullnode.
# However, the wallet chews about half the total memory and is NOT REQUIRED TO ACTUALLY FARM.
# Therefore, Machinaris users can choose leave the wallet service off, periodically running it
# up to sync, gather latest stats, then stop it again for some interval.  When rotated thru
# the full set of blockchains, this can result in a substantial memory usage decrease.
#
 

import datetime

from random import randrange

from api import app
from common.config import globals
from api.commands import chia_cli

RESTART_HOUR_EARLY = randrange(12)
RESTART_HOUR_LATE = RESTART_HOUR_EARLY + 12

def execute():
    blockchain = globals.enabled_blockchains()[0]
    if blockchain in ['chia', 'mmx']:
        return  # Take no action for Chia or MMX at this point, only Chia fork blockchains
    current_hour = datetime.datetime.now().hour
    if not current_hour in [ RESTART_HOUR_EARLY, RESTART_HOUR_LATE]:
        app.logger.info("Not restarting legacy blockchain farmer as currently scheduled for hours {0} and {1}.".format(RESTART_HOUR_EARLY, RESTART_HOUR_LATE))
        return # Don't restart except for twice daily
    with app.app_context():
        try:
            app.logger.info("***************** RESTARTING LEGACY BLOCKCHAIN FARMER!!! ******************")
            chia_cli.start_farmer(blockchain)
        except Exception as ex:
            app.logger.info("Skipping legacy blockchain farmer check due to exception: {0}".format(str(ex)))

def get_wallet_sync_frequency():
    return 3 * 60 # For testing, sync once every 3 hours.
