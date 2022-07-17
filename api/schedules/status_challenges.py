#
# Performs a REST call to controller (possibly localhost) of latest blockchain challenges.
#

import datetime
import os
import traceback

from flask import g

from common.config import globals
from common.models import challenges as c
from common.utils import converters
from api import app
from api.commands import log_parser
from api import utils

def delete_old_challenges(db):
    try:
        cutoff = datetime.datetime.now() - datetime.timedelta(hours=1)
        cutoff_str = "{0}".format(cutoff.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3])
        #app.logger.info("Purging old challenges earlier than {0}".format(cutoff_str))
        db.session.query(c.Challenge).filter(c.Challenge.created_at < cutoff_str).delete()
        db.session.commit()
    except:
        app.logger.info("Failed to delete old challenges.")
        app.logger.info(traceback.format_exc())

def update():
    app.logger.info("Executing status_challenges...")
    with app.app_context():
        from api import db
        if globals.load()['is_controller']:
            delete_old_challenges(db)
        try:
            hostname = utils.get_displayname()
            payload = []
            for blockchain in globals.enabled_blockchains():
                recent_challenges = log_parser.recent_challenges(blockchain)
                if not recent_challenges:
                    return
                for challenge in recent_challenges.rows:
                    payload.append({
                        "unique_id": hostname + '_' + challenge['challenge_id'] + '_' + challenge['created_at'],
                        "hostname": hostname,
                        "blockchain": blockchain,
                        "challenge_id": challenge['challenge_id'],
                        "plots_past_filter": challenge['plots_past_filter'],
                        "proofs_found": challenge['proofs_found'],
                        "time_taken": challenge['time_taken'],
                        "created_at": challenge['created_at'],
                    })
            utils.send_post('/challenges/', payload, debug=False)
        except Exception as ex:
            app.logger.info("Failed to load and send recent challenges because {0}".format(str(ex)))
