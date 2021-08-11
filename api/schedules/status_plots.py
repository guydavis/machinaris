#
# Performs a REST call to controller (possibly localhost) of all plots.
#

import asyncio
import os
import traceback

from flask import g

from common.config import globals
from common.utils import converters
from api import app
from api.commands import chia_cli
from api.rpc import chia
from api import utils

def update():
    if not globals.farming_enabled() and not globals.harvesting_enabled():
        #app.logger.info("Skipping plotting status collection on farming/harvesting instance.")
        return
    with app.app_context():
        try:
            hostname = utils.get_hostname()
            plots_farming = chia_cli.load_plots_farming()
            plots_via_rpc = asyncio.run(chia.get_all_plots())
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
                    plot_rpc_obj = find_plot_obj_by_id(plots_via_rpc, plot_id)
                    payload.append({
                        "plot_id": plot_id,
                        "hostname": hostname,
                        "dir": plot['dir'],
                        "file": plot['file'],
                        "created_at": plot['created_at'],
                        "size": plot['size'],
                        "type": "" if not 'type' in plot_rpc_obj else plot_rpc_obj['type']
                    })
            if len(payload) > 0:
                utils.send_post('/plots/', payload, debug=False)
            else:
                utils.send_delete('/plots/', debug=False)
        except:
            app.logger.info("Failed to load plots farming and send.")
            app.logger.info(traceback.format_exc())

def find_plot_obj_by_id(plots_via_rpc, plot_id):
    for plot_rpc in plots_via_rpc:
        if plot_rpc['plot_id'].startswith("0x{0}".format(plot_id)):
            return plot_rpc
    return None