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

from common.models import plots as p, plottings as pl
from common.models import workers as w
from common.config import globals
from api import app, utils

# If found no valid check for a plot, don't attempt again for at least a week
RETRY_INTERVAL_MINS = 60 * 24 * 7 

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
        app.logger.error("Failed to check age of temp file at: {0}".format(plot_check_log))
        app.logger.error("Due to: {0}".format(str(ex)))
    return False

def open_status_json():
    status = {}
    try:
        if os.path.exists(STATUS_FILE): 
            with open(STATUS_FILE, 'r') as fp:
                status = json.load(fp)
    except Exception as ex:
        app.logger.error("Failed to read JSON from {0} because {1}".format(STATUS_FILE, str(ex)))
    return status

def write_status_json(status):
    with open(STATUS_FILE, 'w+') as fp:
        json.dump(status, fp)

def set_analyze_status(workers, status, plot):
    #app.logger.info("Checking for analyze of {0}".format(plot.plot_id))
    analyze_log = ANALYZE_LOGS + '/' + plot.plot_id[:8] + '.log'
    analysis_seconds = None
    if not os.path.exists(analyze_log):
        [hostname, displayname, result] = request_analyze(plot.file, workers)
        if result:
            with open(analyze_log, 'w+') as f:
                f.write("Plotman analyze from {0} ({1}) found at {2}\n".format(displayname, 
                    hostname, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                f.write(result)
        else:  
            pathlib.Path(analyze_log).touch() # Leave an empty mark file for no result
    with open(analyze_log, 'r+') as f:
        for line in f.readlines():
            #app.logger.info(line)
            if line.startswith("Plotman"): # Header line with hostname
                try:
                    splits = line.split()
                    hostname = splits[4][1:-1] # strip off brackets
                    displayname = splits[3]
                except Exception as ex:
                    app.log.error("Failed to parse plotman analyze header because: {0}".format(str(ex)))
                    app.log.error(line)
            elif line.startswith("| x "):
                try:
                    analysis_seconds = line.split('|')[8].strip()
                except Exception as ex:
                    app.log.error("Failed to parse plotman analyze line because: {0}".format(str(ex)))
                    app.log.error(line)
    if plot.plot_id[:8] in status:
        plot_state = status[plot.plot_id[:8]]
    else:
        plot_state = {}
        status[plot.plot_id[:8]] = plot_state
    if analysis_seconds:
        #app.logger.info("For {0} found {1} seconds.".format(plot.plot_id, analysis_seconds))
        plot_state['analyze'] = { 'host': hostname, 'seconds': analysis_seconds }
    else:
        plot_state['analyze'] = None
 
def request_analyze(plot_file, workers):
    # Don't know which plotter might have the plot result so try them in-turn
    for plotter in workers:
        #app.logger.info("{0}:{1} - {2} - {3}".format(plotter.hostname, plotter.port, plotter.blockchain, plotter.mode))
        if (plotter.mode == 'fullnode' and plotter.blockchain in pl.PLOTTABLE_BLOCKCHAINS) or 'plotter' in plotter.mode:
            if plotter.latest_ping_result != "Responding":
                app.logger.info("Skipping analyze call to {0} as last ping was: {1}".format( \
                    plotter.hostname, plotter.latest_ping_result))
                continue
            try:
                app.logger.info("Trying {0}:{1} for analyze....".format(plotter.hostname, plotter.port))
                payload = {"service":"plotting", "action":"analyze", "plot_file": plot_file }
                response = utils.send_worker_post(plotter, "/analysis/", payload, debug=False)
                if response.status_code == 200:
                    return [plotter.hostname, plotter.displayname, response.content.decode('utf-8')]
                elif response.status_code == 404:
                    app.logger.info("Plotter on {0}:{1} did not have plot log for {2}".format(
                        plotter.hostname, plotter.port, plot_file))
                else:
                    app.logger.info("Plotter on {0}:{1} returned an unexpected error: {2}".format(
                        plotter.hostname, plotter.port, response.status_code))
            except Exception as ex:
                app.logger.error(str(ex))
    return [None, None, None]

def set_check_status(workers, status, plot, refresh):
    check_log = CHECK_LOGS + '/' + plot.plot_id[:8] + '.log'
    check_status = None
    requested_status = False
    if refresh or not os.path.exists(check_log):
        app.logger.info("Requesting plot check of {0}".format(plot.plot_id))
        requested_status = True
        [hostname, displayname, result] = request_check(plot, workers)
        if result:
            with open(check_log, 'w+') as f:
                f.write("Plots check from {0} ({1}) found at {2}\n".format(displayname, 
                    hostname, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                f.write(result)
        else:  
            pathlib.Path(check_log).touch() # Leave an empty mark file for no result
    with open(check_log, 'r+') as f:
        for line in f.readlines():
            #app.logger.info(line)
            if line.startswith("Plots check from "):
                check_status = 'BAD'  # Assume an invalid plot unless get valid line below
                try:
                    splits = line.split()
                    hostname = splits[4][1:-1] # strip off brackets
                    displayname = splits[3]
                except Exception as ex:
                    app.log.error("Failed to parse plots check header because: {0}".format(str(ex)))
                    app.log.error(line)
            elif "Found 1 valid plots" in line:
                check_status = 'GOOD'
    if plot.plot_id[:8] in status:
        plot_state = status[plot.plot_id[:8]]
    else:
        plot_state = {}
        status[plot.plot_id[:8]] = plot_state
    if check_status:
        #app.logger.info("For {0} found {1} status.".format(plot.plot_id, check_status))
        plot_state['check'] = { 'host': hostname, 'status': check_status }
    else:
        plot_state['check'] = None
    return requested_status

def request_check(plot, workers):
    # Don't know which harvester might have the plot result so try them in-turn
    for harvester in workers:
        #app.logger.info("{0}:{1} - {2} - {3}".format(harvester.hostname, harvester.port, harvester.blockchain, harvester.mode))
        if harvester.mode == 'fullnode' or 'harvester' in harvester.mode:
            if harvester.latest_ping_result != "Responding":
                app.logger.info("Skipping check call to {0} as last ping was: {1}".format( \
                    harvester.hostname, harvester.latest_ping_result))
                continue
            if harvester.hostname != plot.hostname or harvester.blockchain != plot.blockchain:
                app.logger.info("Skipping check call to {0} ({1}) for plot on {2} ({3})".format( \
                    harvester.hostname, harvester.blockchain, plot.hostname, plot.blockchain))
                continue
            try:
                app.logger.info("Trying {0}:{1} for plot check....".format(harvester.hostname, harvester.port))
                payload = {"service":"farming", "action":"check", "plot_file": plot.dir + '/' + plot.file }
                response = utils.send_worker_post(harvester, "/analysis/", payload, debug=True)
                if response.status_code == 200:
                    return [harvester.hostname, harvester.displayname, response.content.decode('utf-8')]
                elif response.status_code == 404:
                    app.logger.info("Harvester on {0}:{1} did not have plot check for {2}".format(
                        harvester.hostname, harvester.port, plot.file))
                else:
                    app.logger.info("Harvester on {0}:{1} returned an unexpected error: {2}".format(
                        harvester.hostname, harvester.port, response.status_code))
            except Exception as ex:
                app.logger.info(str(ex))
    return [None, None, None]

def refresh_status_file_from_logs():
    status = open_status_json()
    for key in list(status.keys()):
        if (not 'check' in status[key] or status[key]['check'] is None) and (not 'analyze' in status[key] or status[key]['analyze'] is None):
            app.logger.info("Deleting {0} both".format(key))
            del status[key]
        elif 'check' in status[key] and status[key]['check'] is None:
            app.logger.info("Deleting {0} check".format(key))
            del status[key]['check']
        elif 'analyze' in status[key] and status[key]['analyze'] is None:
            app.logger.info("Deleting {0} analyze".format(key))
            del status[key]['analyze']
    write_status_json(status)

last_retry_time = None
def execute(plot_id=None):
    global last_retry_time
    if 'plots_check_analyze_skip' in os.environ and os.environ['plots_check_analyze_skip'].lower() == 'true':
        app.logger.info("Skipping plots check and analyze as environment variable 'plots_check_analyze_skip' is present.")
        return
    if not last_retry_time or last_retry_time <= \
        (datetime.datetime.now() - datetime.timedelta(minutes=RETRY_INTERVAL_MINS)):
        last_retry_time = datetime.datetime.now()  # Delete any empty markers allowing a retry once a day.
        os.system("/usr/bin/find /root/.chia/plotman/checks/ -type f -empty -print -delete")
        refresh_status_file_from_logs()
    with app.app_context():
        from api import db
        gc = globals.load()
        if not gc['is_controller']:
            return # Only controller should initiate check/analyze against other fullnodes/harvesters
        try:
            if not os.path.isdir(ANALYZE_LOGS):
                os.makedirs(ANALYZE_LOGS)
            if not os.path.isdir(CHECK_LOGS):
                os.makedirs(CHECK_LOGS)
        except Exception as ex:
            app.logger.info("Unable to create analyze and check folders in plotman. {0}".format(str(ex)))
        workers = db.session.query(w.Worker)
        if plot_id:
            plots = db.session.query(p.Plot).filter(p.Plot.plot_id == plot_id).all()
        else:    
            plots = db.session.query(p.Plot).filter(or_(p.Plot.plot_check.is_(None), 
                p.Plot.plot_analyze.is_(None))).order_by(p.Plot.created_at.desc()).all()
        status = open_status_json()
        requested_status_count = 0
        #app.logger.info("Querying for plots...")
        for plot in plots:
            #app.logger.info("Checking plot {0}".format(plot.plot_id))
            set_analyze_status(workers, status, plot)
            if os.environ['blockchains'][0] == 'mmx':
                continue # Skip over MMX plots as they can't be checked
            if set_check_status(workers, status, plot, plot_id != None):
                requested_status_count += 1
            if requested_status_count > 5:  # Only remote request `check plots` on at most 5 plots per cycle
                break
        write_status_json(status)