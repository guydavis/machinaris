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
from sqlalchemy import or_

from common.models import plots as p
from common.config import globals
from api import app, utils

#
#
#
def have_recent_plot_check_log(plot_check_log):
    try:
        if os.path.exists(plot_check_log):
            created_date = time.ctime(os.path.getctime(plot_check_log))
            month_ago = datetime.datetime.now() - datetime.timedelta(months=1)
            return created_date > month_ago  # False if last check was over a month ago
    except Exception as ex:
        app.logger.info("Failed to check age of temp file at: {0}".format(path))
        app.logger.info("Due to: {0}".format(str(ex)))
    return False

def execute():
    with app.app_context():
        from api import db
        gc = globals.load()
        if not gc['is_controller']:
            return # Only controller should initiate check/analyze against other fullnodes/harvesters
        #plots = db.session.query(p.Plot).filter(p.Plot.blockchain == gc['enabled_blockchains'][0], 
        #    or_(p.Plot.check is None, p.Plot.analyze is None)).order_by(p.Plot.created_at.desc).limit(100)
        #for plot in plots:
            # Check for analyze output on disk at /root/.chia/plotman/analzye/PLOT_ID.log (empty means nothing)
            # If no file, found invoke analyze to check with harvesters.
            # Store the total time in seconds into a table in the stats database.  Delete all 100 earlier records each time.
            #plot_check_log = f'/root/.chia/plotman/checks/{plot_file}.log'
            #os.makedirs(os.path.dirname(plot_check_log))