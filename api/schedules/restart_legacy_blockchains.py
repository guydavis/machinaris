#
# On a farmer, restarts the fullnode for out-of-date blockchain forks twice daily in 
# an attempt to keep their memory usage under control.  Many of these forks are running
# Chia code from 2021, so are missing a many, many optimizations in more recent versions.
# Restarts different blockchains at different hours of the day to spread out memory bumps
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
    if not globals.legacy_blockchain(blockchain):
        return # Don't restart Chia and recently-updated blockchains.
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