#
# Performs a REST call to controller (possibly localhost) of latest blockchain partials.
#

import datetime
import os
import traceback

from flask import g

from common.config import globals
from common.models import partials as p
from common.utils import converters
from api import app
from api.commands import log_parser
from api import utils

def delete_old_partials(db):
    try:
        cutoff = datetime.datetime.now() - datetime.timedelta(days=1)
        cutoff_str = "{0}".format(cutoff.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3])
        app.logger.debug("Purging old partials earlier than {0}".format(cutoff_str))
        db.session.query(p.Partial).filter(p.Partial.created_at < cutoff_str).delete()
        db.session.commit()
    except:
        app.logger.info("Failed to delete old partials.")
        app.logger.info(traceback.format_exc())

def update():
    with app.app_context():
        try:
            from api import db
            delete_old_partials(db)
            hostname = utils.get_hostname()
            payload = []
            partials_so_far = {}
            for blockchain in globals.enabled_blockchains():
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
