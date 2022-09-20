#
# Performs a REST call to controller (possibly localhost) for any recent warnings.
#

import json
import os
import traceback

from flask import g

from common.config import globals
from common.utils import converters
from api import app
from api.commands import rpc
from api import utils

def collect():
    with app.app_context():
        blockchain = globals.enabled_blockchains()[0]
        try:
            if blockchain == 'chia':
                warnings = rpc.RPC().get_harvester_warnings()
                for host in warnings.keys():
                    for type in ['invalid_plots', 'missing_keys', 'duplicate_plots']:
                        bad_plots = warnings[host][type]
                        payload = []
                        mapped_hostname = utils.convert_chia_ip_address(host)
                        if bad_plots:
                            payload.append({
                                "hostname": mapped_hostname,
                                "blockchain": blockchain,
                                "type": type,
                                "service": "harvester",
                                "title": type,
                                "content": json.dumps(bad_plots),
                            })
                            utils.send_post('/warnings/{0}/{1}/{2}'.format(mapped_hostname, blockchain, type), payload, debug=False)
                        else:
                            utils.send_delete('/warnings/{0}/{1}/{2}'.format(mapped_hostname, blockchain, type), debug=False)
        except Exception as ex:
            app.logger.info("Failed to load and send warnings because {0}".format(str(ex)))
            traceback.print_exc()
