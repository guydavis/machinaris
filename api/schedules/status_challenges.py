#
# Performs a REST call to controller (possibly localhost) of latest blockchain challenges.
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
        #app.logger.info("Skipping recent challenges collection on plotting-only instance.")
        return
    with app.app_context():
        try:
            hostname = utils.get_hostname()
            recent_challenges = log_parser.recent_challenges()
            payload = []
            for challenge in recent_challenges.rows:
                payload.append({
                    "unique_id": hostname + '_' + challenge['challenge_id'] + '_' + challenge['created_at'],
                    "hostname": hostname,
                    "challenge_id": challenge['challenge_id'],
                    "plots_past_filter": challenge['plots_past_filter'],
                    "proofs_found": challenge['proofs_found'],
                    "time_taken": challenge['time_taken'],
                    "created_at": challenge['created_at'],
                })
            utils.send_post('/challenges/', payload, debug=False)
        except:
            app.logger.info("Failed to load recent challenges and send.")
            app.logger.info(traceback.format_exc())
