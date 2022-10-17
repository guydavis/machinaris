#
# Performs a twice-daily NFT reward recovery using fd-cli: https://github.com/Flora-Network/flora-dev-cli
#

import datetime
import os
import sqlite3
import time
import traceback

from flask import g

from common.models import wallets as w, plotnfts as p, workers as wk
from common.config import globals
from api import app, utils
from api.commands import rewards

def execute():
    with app.app_context():
        from api import db
        gc = globals.load()
        app.logger.info("****************** Starting hourly NFT 7/8 qualified reward coins check... *********************")
        rewards.update_qualified_coins_cache()
