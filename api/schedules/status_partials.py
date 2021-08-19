#
# Performs a REST call to controller (possibly localhost) of latest blockchain partials.
#

import os
import traceback

from flask import g

from common.config import globals
from common.utils import converters
from api import app
from api.commands import log_parser
from api import utils

def update():
    if not globals.farming_enabled() and not globals.harvesting_enabled():
        #app.logger.info("Skipping recent partials collection on plotting-only instance.")
        return
    with app.app_context():
        try:
            hostname = utils.get_hostname()
            blockchains = ['chia']
            if globals.flax_enabled():
                blockchains.append('flax')
            payload = []
            partials_so_far = {}
            for blockchain in blockchains:
                recent_partials = log_parser.recent_partials(blockchain)
                for partial in recent_partials.rows:
                    app.logger.debug(partial)
                    unique_id = hostname + '_' + partial['launcher_id'] + '_' + partial['created_at']
                    if unique_id in partials_so_far:
                        app.logger.debug("Skipping duplicate partial: {0}".format(unique_id))
                    else:
                        partials_so_far[unique_id] = partial
                        payload.append({
                            "unique_id": unique_id,
                            "hostname": hostname,
                            "blockchain": blockchain,
                            "launcher_id": partial['launcher_id'],
                            "pool_url": partial['pool_url'],
                            "pool_response": partial['pool_response'],
                            "created_at": partial['created_at'],
                        })
            app.logger.debug(payload)
            utils.send_post('/partials/', payload, debug=False)
        except:
            app.logger.info("Failed to load recent partials and send.")
            app.logger.info(traceback.format_exc())
