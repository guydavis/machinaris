#
# For all new plots, check to see if a plotman analyze exists
# Store most recent plot times in the stats database.
#

import datetime
import os
import sqlite3
import time
import traceback

from flask import g

from common.models import plots as p
from common.config import globals
from api import app, utils

def execute():
    with app.app_context():
        from api import db
        gc = globals.load()
        blockchain = os.environ['blockchains']
        if not os.environ['mode'] == 'fullnode' or not os.environ['blockchains']  == 'chia':
            return # Only Chia controller should analyze plots
        #plots = db.session.query(p.Plot).filter(p.Plot.blockchain == blockchain).order_by(p.Plot.created_at.desc).limit(100)
        #for plot in plots:
            # Check for analyze output on disk at /root/.chia/plotman/analzye/PLOT_ID.log (empty means nothing)
            # If no file, found invoke analyze to check with harvesters.
            # Store the total time in seconds into a table in the stats database.  Delete all 100 earlier records each time.
            