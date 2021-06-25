#
# Performs a REST call to controller (possibly localhost) of all plots.
#

import os
import traceback

from flask import g

from common.config import globals
from common.utils import converters
from api import app
from api.commands import chia_cli
from api import utils

def update():
    if not globals.farming_enabled() and not globals.harvesting_enabled():
        #app.logger.info("Skipping plotting status collection on farming/harvesting instance.")
        return
    with app.app_context():
        try:
            hostname = utils.get_hostname()
            plots_farming = chia_cli.load_plots_farming()
            payload = []
            for plot in plots_farming.rows:
                payload.append({
                    "plot_id": plot['plot_id'],
                    "hostname": hostname,
                    "dir": plot['dir'],
                    "file": plot['file'],
                    "created_at": plot['created_at'],
                    "size": plot['size'],
                })
            if len(payload) > 0:
                utils.send_post('/plots/', payload, debug=False)
            else:
                utils.send_delete('/plots/', debug=False)
        except:
            app.logger.info("Failed to load plots farming and send.")
            app.logger.info(traceback.format_exc())
