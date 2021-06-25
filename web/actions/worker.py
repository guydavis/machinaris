#
# Actions around managing distributed workers and their status.
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
from common.models import workers as w
from common.config import globals
from web.models.worker import WorkerSummary

ALL_TABLES_BY_HOSTNAME = [
    'alerts',
    'blockchains',
    'challenges',
    'connections',
    'farms', 
    'keys',
    'plots',
    'plottings',
    'wallets',
    'workers'
]


def load_worker_summary():
    workers = db.session.query(w.Worker).order_by(w.Worker.hostname).all()
    return WorkerSummary(workers)

def get_worker_by_hostname(hostname):
    #app.logger.info("Searching for worker with hostname: {0}".format(hostname))
    return db.session.query(w.Worker).get(hostname)

def prune_workers_status(hostnames):
    for hostname in hostnames:
        for table in ALL_TABLES_BY_HOSTNAME:
            db.session.execute("DELETE FROM " + table + " WHERE hostname = :hostname", {"hostname":hostname})
            db.session.commit()
