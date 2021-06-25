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

def get_log_lines(worker, log_type, log_id):
    try:
        payload = {"type": log_type }
        if log_id != 'undefined':
            payload['log_id'] = log_id
        response = utils.send_get(worker, "/logs/{0}".format(log_type), payload, debug=False)
        return response.content.decode('utf-8')
    except:
        app.logger.info(traceback.format_exc())
        return 'Failed to load log file from {0}'.format(worker.hostname)
