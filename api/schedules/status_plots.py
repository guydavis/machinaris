#
# Performs a REST call to controller (possibly localhost) of all plots.
#

import datetime
import os
import traceback

from flask import g

from common.config import globals
from common.utils import converters
from api import app
from api.commands import chia_cli
from api import utils

# Due to load, only send full plots list every X minutes
FULL_SEND_INTERVAL_MINS = 15

last_full_send_time = None

def update():
    global last_full_send_time
    if not globals.farming_enabled() and not globals.harvesting_enabled():
        #app.logger.info("Skipping plotting status collection on farming/harvesting instance.")
        return
    with app.app_context():
        try:
            since = (datetime.datetime.now() - datetime.timedelta(minutes=FULL_SEND_INTERVAL_MINS)).strftime("%Y-%m-%d %H:%M:%S.000")
            if not last_full_send_time or last_full_send_time <= \
                (datetime.datetime.now() - datetime.timedelta(minutes=FULL_SEND_INTERVAL_MINS)):
                since = None  # No since filter sends all plots, not just recent
                last_full_send_time = datetime.datetime.now()
            hostname = utils.get_hostname()
            plots_farming = chia_cli.load_plots_farming()
            plots_by_id = {}
            payload = []
            for plot in plots_farming.rows:
                plot_id = plot['plot_id']
                if plot_id in plots_by_id:
                    other_plot = plots_by_id[plot_id]
                    app.logger.info("Skipping addition of plot at {0}/{1} because same plot_id found at {2}/{3}".format(
                        plot['dir'], plot['file'], other_plot['dir'], other_plot['file']))
                else: # No conflict so add it to plots list
                    plots_by_id[plot_id] = plot
                    if not since or plot['created_at'] > since:
                        payload.append({
                            "plot_id": plot_id,
                            "hostname": hostname,
                            "dir": plot['dir'],
                            "file": plot['file'],
                            "created_at": plot['created_at'],
                            "size": plot['size']
                        })
            if len(payload) > 0:
                utils.send_post('/plots/', payload, debug=False)
        except:
            app.logger.info("Failed to load plots farming and send.")
            app.logger.info(traceback.format_exc())
