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
from api.schedules import common

def update():
    if not globals.is_fullnode() or not globals.plotting_enabled():
        app.logger.info(
            "Skipping plotting stats collection on plottinging/harvesting instance.")
        return
    with app.app_context():
        try:
            hostname = common.get_hostname()
            plotting_summary = plotman_cli.load_plotting_summary()
            # TODO Query for current set and delete any stale/completed records
            for plot in plotting_summary.rows:
                payload = {
                    "plot_id": plot['plot_id'],
                    "hostname": hostname,
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
                }
                common.send_post('/plottings', payload, debug=True)
        except:
            app.logger.info("Failed to load plotting summary and send.")
            app.logger.info(traceback.format_exc())
