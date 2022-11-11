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
    with app.app_context():
        try:
            hostname = utils.get_hostname()
            blockchain = globals.enabled_blockchains()[0]
            archiving_summary = plotman_cli.load_archiving_summary()
            if not archiving_summary:
                return
            payload = []
            for transfer in archiving_summary:
                payload.append({
                    "plot_id": transfer['plot_id'],
                    "hostname": hostname,
                    "blockchain": blockchain,
                    "k": transfer['k'],
                    "size": transfer['size'],
                    "source": transfer['source'],
                    "dest": transfer['dest'],
                    "status": transfer['status']
                })
            if len(payload) > 0:
                utils.send_post('/transfers/{0}/{1}'.format(hostname, blockchain), payload, debug=False)
            else:
                utils.send_delete('/transfers/{0}/{1}'.format(hostname, blockchain), debug=False)
        except Exception as ex:
            app.logger.info("Failed to load and send plotting jobs because {0}".format(str(ex)))
