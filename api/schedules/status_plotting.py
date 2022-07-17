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
    app.logger.info("Executing status_plotting...")
    with app.app_context():
        try:
            hostname = utils.get_hostname()
            blockchain = globals.enabled_blockchains()[0]
            plotting_summary = plotman_cli.load_plotting_summary()
            if not plotting_summary:
                return
            payload = []
            for plot in plotting_summary.rows:
                payload.append({
                    "plot_id": plot['plot_id'],
                    "hostname": hostname,
                    "blockchain": blockchain,
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
                utils.send_post('/plottings/{0}/{1}'.format(hostname, blockchain), payload, debug=False)
            else:
                utils.send_delete('/plottings/{0}/{1}'.format(hostname, blockchain), debug=False)
        except Exception as ex:
            app.logger.info("Failed to load and send plotting jobs because {0}".format(str(ex)))
