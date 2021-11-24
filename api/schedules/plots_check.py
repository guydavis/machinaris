#
# For all new plots, check to see if a plotman analyze exists
# Store most recent plot times in the stats database.
#

import datetime
import json
import pathlib
import os
import sqlite3
import time
import traceback

from flask import g
from sqlalchemy import or_

from common.models import plots as p
from common.models import workers as w
from common.config import globals
from api import app, utils

STATUS_FILE = '/root/.chia/plotman/status.json'
ANALYZE_LOGS = '/root/.chia/plotman/analyze'
CHECK_LOGS = '/root/.chia/plotman/checks'

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

def open_status_json():
    status = {}
    if os.path.exists(STATUS_FILE): 
        with open(STATUS_FILE, 'r+') as fp:
            status = json.load(fp)
    return status

def write_status_json(status):
    with open(STATUS_FILE, 'w+') as fp:
        json.dump(status, fp)

def set_analyze_status(workers, status, plot):
    analyze_log = ANALYZE_LOGS + '/' + plot.plot_id + '.log'
    if not os.path.exists(analyze_log):
        result = request_analyze(plot.plot_file, workers)
        if result:
            pass
            # Save the result to a file
            # Store the analysis time into the status.json
        #else:   
        #    pathlib.Path(analyze_log).touch() # Leave an empty mark file for no result
    else:
        # if empty file, leave none
        # if file has analyze, store the analysis time into the status.json
        pass
            

def request_analyze(plot_file, workers):
    # Don't know which plotter might have the plot result so try them in-turn
    for plotter in workers:
        #app.logger.info("{0}:{1} - {2} - {3}".format(plotter.hostname, plotter.port, plotter.blockchain, plotter.mode))
        if plotter.mode == 'fullnode' or 'plotter' in plotter.mode:
            if plotter.latest_ping_result != "Responding":
                app.logger.info("Skipping analyze call to {0} as last ping was: {1}".format( \
                    plotter.hostname, plotter.latest_ping_result))
                continue
            try:
                app.logger.info("Trying {0}:{1} for analyze....".format(plotter.hostname, plotter.port))
                payload = {"service":"plotting", "action":"analyze", "plot_file": plot_file }
                response = utils.send_post(plotter, "/analysis/", payload, debug=False)
                if response.status_code == 200:
                    return response.content.decode('utf-8')
                elif response.status_code == 404:
                    app.logger.info("Plotter on {0}:{1} did not have plot log for {2}".format(
                        plotter.hostname, plotter.port, plot_file))
                else:
                    app.logger.info("Plotter on {0}:{1} returned an unexpected error: {2}".format(
                        plotter.hostname, plotter.port, response.status_code))
            except:
                app.logger.info(traceback.format_exc())
    return None

def execute():
    with app.app_context():
        from api import db
        gc = globals.load()
        if not gc['is_controller']:
            return # Only controller should initiate check/analyze against other fullnodes/harvesters
        workers = db.session.query(w.Worker)
        plots = db.session.query(p.Plot).filter(p.Plot.blockchain == gc['enabled_blockchains'][0], 
            or_(p.Plot.check is None, p.Plot.analyze is None)).order_by(p.Plot.created_at.desc()).limit(1)
        status = open_status_json()
        for plot in plots:
            set_analyze_status(workers, status, plot)
            # Check for analyze output on disk at /root/.chia/plotman/analzye/PLOT_ID.log (empty means nothing)
            # If no file, found invoke analyze to check with harvesters.
            # Store the total time in seconds into a table in the stats database.  Delete all 100 earlier records each time.
            #plot_check_log = f'/root/.chia/plotman/checks/{plot_file}.log'
            #os.makedirs(os.path.dirname(plot_check_log))
        write_status_json(status)