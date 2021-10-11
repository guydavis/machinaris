#
# Performs a REST call to controller (possibly localhost) of all plots.
#

import datetime
import os
import re
import traceback

from flask import g

from common.config import globals
from common.models import plots as p
from api import app, db
from api.rpc import chia
from api import utils

# Due to database load, only send full plots list every X minutes
FULL_SEND_INTERVAL_MINS = 15

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

def update():
    global last_full_send_time
    with app.app_context():
        since = (datetime.datetime.now() - datetime.timedelta(minutes=FULL_SEND_INTERVAL_MINS)).strftime("%Y-%m-%d %H:%M")
        if not last_full_send_time or last_full_send_time <= \
            (datetime.datetime.now() - datetime.timedelta(minutes=FULL_SEND_INTERVAL_MINS)):
            since = None  # No since filter sends all plots, not just recent
            last_full_send_time = datetime.datetime.now()
        if 'chia' in globals.enabled_blockchains():
            update_chia_plots(since)
        elif 'chives' in globals.enabled_blockchains():
            update_chives_plots(since)
        else:
            app.logger.debug("Skipping plots update from blockchains other than chia and chives as they all farm same as chia.")

def update_chia_plots(since):
    try:
        controller_hostname = utils.get_hostname()
        plots_farming = chia.get_all_plots()
        payload = []
        for plot in plots_farming:
            short_plot_id,dir,file,created_at = get_plot_attrs(plot['plot_id'], plot['filename'])
            if not since or created_at > since:
                payload.append({
                    "plot_id": short_plot_id,
                    "blockchain": 'chia',
                    # '172.17.0.2' was weird non-local IP on OlivierLA75's Docker setup, inside his container
                    "hostname": controller_hostname if plot['hostname'] in ['127.0.0.1', '172.17.0.2']  else plot['hostname'],
                    "dir": dir,
                    "file": file,
                    "type": plot['type'],
                    "created_at": created_at,
                    "size": plot['file_size']
                })
        if not since:  # If no filter, delete all before sending all current again
            db.session.query(p.Plot).delete()
        if len(payload) > 0:
            for new_item in payload:
                item = p.Plot(**new_item)
                db.session.add(item)
        db.session.commit()
    except:
        app.logger.info("Failed to load plots farming and send.")
        app.logger.info(traceback.format_exc())

def update_chives_plots(since):
    try:
        controller_hostname = utils.get_hostname()
        plots_farming = chia.get_all_plots()
        payload = []
        for plot in plots_farming:
            short_plot_id,dir,file,created_at = get_plot_attrs(plot['plot_id'], plot['filename'])
            if not since or created_at > since:
                payload.append({
                    "plot_id": short_plot_id,
                    "blockchain": 'chives',
                    "hostname": controller_hostname if plot['hostname'] in ['127.0.0.1'] else plot['hostname'],
                    "dir": dir,
                    "file": file,
                    "type": plot['type'],
                    "created_at": created_at,
                    "size": plot['file_size']
                })
        if not since:  # If no filter, delete all before sending all current again
            db.session.query(p.Plot).delete()
        if len(payload) > 0:
            for new_item in payload:
                item = p.Plot(**new_item)
                db.session.add(item)
        db.session.commit()
    except:
        app.logger.info("Failed to load plots farming and send.")
        app.logger.info(traceback.format_exc())