#
# Performs a REST call to controller (possibly localhost) of all plots.
#

import datetime
import json
import os
import re
import traceback

from flask import g

from common.config import globals
from common.models import plots as p
from common.models import workers as w
from api import app, db
from api.rpc import chia
from api import utils

# Due to database load, only send full plots list every X minutes
FULL_SEND_INTERVAL_MINS = 15

# Holds the cached status of Plotman analyze and Chia plots check
STATUS_FILE = '/root/.chia/plotman/status.json'

last_full_send_time = None

def get_plot_attrs(plot_id, filename):
    short_plot_id = plot_id[2:10]
    dir,file = os.path.split(filename)
    match = re.match("plot-k(\d+)-(\d+)-(\d+)-(\d+)-(\d+)-(\d+)-(\w+).plot", file)
    if match:
        created_at = "{0}-{1}-{2} {3}:{4}".format( match.group(2),match.group(3),match.group(4),match.group(5),match.group(6))
    else:
        created_at = "" 
    return [short_plot_id, dir,file,created_at]

def open_status_json():
    status = {}
    if os.path.exists(STATUS_FILE): 
        with open(STATUS_FILE, 'r+') as fp:
            status = json.load(fp)
    return status

def update():
    global last_full_send_time
    with app.app_context():
        since = (datetime.datetime.now() - datetime.timedelta(minutes=FULL_SEND_INTERVAL_MINS)).strftime("%Y-%m-%d %H:%M")
        if not last_full_send_time or last_full_send_time <= \
            (datetime.datetime.now() - datetime.timedelta(minutes=FULL_SEND_INTERVAL_MINS)):
            since = None  # No since filter sends all plots, not just recent
            last_full_send_time = datetime.datetime.now()
        if 'chia' in globals.enabled_blockchains():
            plots_status = open_status_json()
            update_chia_plots(plots_status, since)
        elif 'chives' in globals.enabled_blockchains():
            update_chives_plots(since)
        else:
            app.logger.debug("Skipping plots update from blockchains other than chia and chives as they all farm same as chia.")

def update_chia_plots(plots_status, since):
    try:
        controller_hostname = utils.get_hostname()
        plots_farming = chia.get_all_plots()
        payload = []
        displaynames = {}
        for plot in plots_farming:
            if plot['hostname'] in displaynames:
                displayname = displaynames[plot['hostname']]
            else: # Look up displayname
                try:
                    hostname = plot['hostname']
                    # '172.18.0.1' was non-local IP on OlivierLA75's Docker setup, inside his container
                    if plot['hostname'] in ['127.0.0.1','172.18.0.1']:
                        hostname = controller_hostname
                    #app.logger.info("Found worker with hostname '{0}'".format(hostname))
                    displayname = db.session.query(w.Worker).filter(w.Worker.hostname==hostname, 
                        w.Worker.blockchain=='chia').first().displayname
                except:
                    app.logger.info("status_plots: Unable to find a worker with hostname '{0}'".format(plot['hostname']))
                    displayname = plot['hostname']
                displaynames[plot['hostname']] = displayname
            short_plot_id,dir,file,created_at = get_plot_attrs(plot['plot_id'], plot['filename'])
            if not since or created_at > since:
                payload.append({
                    "plot_id": short_plot_id,
                    "blockchain": 'chia',
                    "hostname": controller_hostname if plot['hostname'] in ['127.0.0.1','172.18.0.1'] else plot['hostname'],
                    "displayname": displayname,
                    "dir": dir,
                    "file": file,
                    "type": plot['type'],
                    "created_at": created_at,
                    "plot_analyze": analyze_status(plots_status, short_plot_id),
                    "plot_check": check_status(plots_status, short_plot_id),
                    "size": plot['file_size']
                })
        if not since:  # If no filter, delete all for this blockchain before sending again
            db.session.query(p.Plot).filter(p.Plot.blockchain=='chia').delete()
        if len(payload) > 0:
            for new_item in payload:
                item = p.Plot(**new_item)
                db.session.add(item)
        db.session.commit()
    except:
        app.logger.info("Failed to load plots farming and send.")
        app.logger.info(traceback.format_exc())

# Sent from a separate fullnode container
def update_chives_plots(since):
    try:
        blockchain = 'chives'
        hostname = utils.get_hostname()
        plots_farming = chia.get_all_plots()
        payload = []
        for plot in plots_farming:
            short_plot_id,dir,file,created_at = get_plot_attrs(plot['plot_id'], plot['filename'])
            if not since or created_at > since:
                payload.append({
                    "plot_id": short_plot_id,
                    "blockchain": blockchain,
                    "hostname": hostname if plot['hostname'] in ['127.0.0.1'] else plot['hostname'],
                    "displayname": None,  # Can't know all Chives workers' displaynames here, done in API receiver
                    "dir": dir,
                    "file": file,
                    "type": plot['type'],
                    "created_at": created_at,
                    "plot_analyze": None, # Handled in receiver
                    "plot_check": None, # Handled in receiver
                    "size": plot['file_size']
                })
        if not since:  # If no filter, delete all before sending all current again
            utils.send_delete('/plots/{0}/{1}'.format(hostname, blockchain), debug=False)
        if len(payload) > 0:
            utils.send_post('/plots/', payload, debug=False)
    except:
        app.logger.info("Failed to load Chives plots farming and send.")
        app.logger.info(traceback.format_exc())

def analyze_status(plots_status, short_plot_id):
    if short_plot_id in plots_status:
        if "analyze" in plots_status[short_plot_id]:
            if plots_status[short_plot_id]['analyze'] and 'seconds' in plots_status[short_plot_id]['analyze']:
                return plots_status[short_plot_id]['analyze']['seconds']
            else:
                return "-"
    return None

def check_status(plots_status, short_plot_id):
    if short_plot_id in plots_status:
        if "check" in plots_status[short_plot_id]:
            if plots_status[short_plot_id]['check'] and 'status' in plots_status[short_plot_id]['check']:
                return plots_status[short_plot_id]['check']['status']
            else:
                return "-"
    return None
