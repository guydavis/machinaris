#
# CLI access to Farmr binary - https://github.com/gilnobrega/farmr
#

import datetime
import json
import os
import sqlite3
import time
import traceback

from common.config import globals
from api import app

def load_device_id():
    if os.path.exists('/root/.farmr/id.json'):
        try:
            id_json = json.load(open('/root/.farmr/id.json'))
        except Exception as ex:
            app.logger.error("Farmr id.json malformed: {0}".format(str(ex)))
            return None
        try:
            id = id_json['ids'][0]
            blockchain = os.environ['blockchains']
            return "{0}-{1}".format(id, globals.get_blockchain_symbol(blockchain).lower())
        except Exception as ex:
            app.logger.error("Farmr id.json missing ids: {0}".format(str(ex)))
            app.logger.info(id_json)
    return None
