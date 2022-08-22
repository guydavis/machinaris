#
# Performs a REST call to controller (possibly localhost) for any recent warnings.
#

import os
import traceback

from flask import g

from common.config import globals
from common.utils import converters
from api import app
from api.commands import rpc
from api import utils

def collect():
    app.logger.info("Executing status_warnings...")
    with app.app_context():
        hostname = utils.get_hostname()
        blockchain = globals.enabled_blockchains()[0]
        try:
            if blockchain == 'chia':
                warnings = rpc.RPC().get_harvester_warnings()
            #payload = {
            #    "hostname": hostname,
            #    "blockchain": blockchain,
            #}
            #utils.send_post('/warnings/', payload, debug=False)
        except Exception as ex:
            app.logger.info("Failed to load and send warnings because {0}".format(str(ex)))
