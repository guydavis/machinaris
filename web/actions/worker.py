#
# Actions around managing distributed workers and their status.
#

import asyncio
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
from web.rpc import chia

ALL_TABLES_BY_HOSTNAME = [
    'alerts',
    'blockchains',
    'challenges',
    'connections',
    'farms', 
    'keys',
    'plotnfts',
    'plots',
    'plottings',
    'pools',
    'wallets',
    'workers'
]

def load_worker_summary(hostname = None):
    query = db.session.query(w.Worker).order_by(w.Worker.displayname)
    if hostname:
        workers = query.filter(w.Worker.hostname==hostname)
    else:
        workers = query.all()
    return WorkerSummary(workers)

def get_worker_by_hostname(hostname):
    #app.logger.info("Searching for worker with hostname: {0}".format(hostname))
    return db.session.query(w.Worker).get(hostname)

def prune_workers_status(hostnames):
    for hostname in hostnames:
        worker = get_worker_by_hostname(hostname)
        for table in ALL_TABLES_BY_HOSTNAME:
            db.session.execute("DELETE FROM " + table + " WHERE hostname = :hostname OR hostname = :displayname", 
                {"hostname":hostname, "displayname":worker.displayname})
            db.session.commit()

class WorkerWarning:

    def __init__(self, title, message, level="info"):
        self.title = title
        self.message = message
        if level == "info":
            self.icon = "info-circle"
        elif level == "error":
            self.icon = "exclamation-circle"

def generate_warnings(worker, plots):
    warnings = []
    # TODO - Warning for harvester not connected (worker but not in farm summary)
    # TODO - Warning for harvester not responding quickly enough
    # TODO - Warning for harvester not responding often enough
    # TODO - Warning for plotter disk usage too high?
    # TODO - Warning if any blockchain challenges are higher than 5 seconds (show both hostname AND drive)
    # TODO - Warning if any blockchain challenges are missing in last hour (some percentage like that chart)
    # TODO - Warning if worker's Machinaris version does not match that of the fullnode
    # TODO - Warning if worker's time drifts more than 3 minutes off fullnode's WHEN responding with ping seconds ago
    return warnings
