#
# Performs a REST call to controller (possibly localhost) of latest plotting status.
#

import os
import traceback

from flask import g

from common.config import globals
from common.utils import converters
from api import app
from api.commands import plotman_cli
from api import utils

def update():
    if not globals.plotting_enabled():
        #app.logger.info("Skipping plotting status collection on farming/harvesting instance.")
        return
    with app.app_context():
        try:
            hostname = utils.get_hostname()
            plotting_summary = plotman_cli.load_plotting_summary()
            payload = []
            for plot in plotting_summary.rows:
                payload.append({
                    "plot_id": plot['plot_id'],
                    "hostname": hostname,
                    "plotter": plot['plotter'],
                    "k": plot['k'],
                    "tmp": plot['tmp'],
                    "dst": plot['dst'],
                    "wall": plot['wall'],
                    "phase": plot['phase'],
                    "size": plot['size'],
                    "pid": plot['pid'],
                    "stat": plot['stat'],
                    "mem": plot['mem'],
                    "user": plot['user'],
                    "sys": plot['sys'],
                    "io": plot['io'],
                })
            if len(payload) > 0:
                utils.send_post('/plottings/', payload, debug=False)
            else:
                utils.send_delete('/plottings/{0}'.format(hostname), debug=False)
        except:
            app.logger.info("Failed to load plotting summary and send.")
            app.logger.info(traceback.format_exc())
