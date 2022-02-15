#
# Actions around access to logs on distributed workers.
#

import datetime
import os
import psutil
import re
import signal
import shutil
import socket
import time
import traceback
import yaml

from flask import Flask, jsonify, abort, request, flash

from web import app, db, utils

def get_log_lines(lang, worker, log_type, log_id, blockchain):
    try:
        payload = {"type": log_type }
        if log_id != 'undefined':
            payload['log_id'] = log_id
        if blockchain != 'undefined':
            payload['blockchain'] = blockchain
        response = utils.send_get(lang, worker, "/logs/{0}".format(log_type), payload, debug=True)
        return response.content.decode('utf-8')
    except:
        app.logger.info(traceback.format_exc())
        return 'Failed to load log file from {0}:{1} running {2}'.format(worker.hostname, worker.port, blockchain)
