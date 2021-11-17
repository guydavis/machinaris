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
from web.models.worker import WorkerSummary
from web.actions import stats

ALL_TABLES_BY_HOSTNAME_AND_BLOCKCHAIN = [
    'alerts',
    'blockchains',
    'challenges',
    'connections',
    'farms', 
    'keys',
    'plots',
    'plottings',
    'plotnfts',
    'pools',
    'wallets',
    'workers'
]

def load_worker_summary(hostname = None):
    query = db.session.query(w.Worker).order_by(w.Worker.displayname, w.Worker.blockchain)
    if hostname:
        workers = query.filter(w.Worker.hostname==hostname)
    else:
        workers = query.all()
    return WorkerSummary(workers)

def get_worker(hostname, blockchain='chia'):
    #app.logger.info("Searching for worker with hostname: {0} and blockchain: {1}".format(hostname, blockchain))
    return db.session.query(w.Worker).filter(w.Worker.hostname==hostname, w.Worker.blockchain==blockchain).first()

def prune_workers_status(workers):
    for id in workers:
        [hostname,blockchain] = id.split('|')
        worker = get_worker(hostname, blockchain)
        if worker:
            if 'chia' == blockchain:
                stats.prune_workers_status(hostname, worker.displayname, worker.blockchain)
            for table in ALL_TABLES_BY_HOSTNAME_AND_BLOCKCHAIN:
                db.session.execute("DELETE FROM " + table + " WHERE (hostname = :hostname OR hostname = :displayname) AND blockchain = :blockchain", 
                    {"hostname":hostname, "displayname":worker.displayname, "blockchain":worker.blockchain})
                db.session.commit()
        else:
            app.logger.info("Unable to find worker: {0} - {1}".format(hostname, blockchain))

class WorkerWarning:

    def __init__(self, title, message, level="info"):
        self.title = title
        self.message = message
        if level == "info":
            self.icon = "info-circle"
        elif level == "error":
            self.icon = "exclamation-circle"

def generate_warnings(worker):
    warnings = []
    # Check if worker is responding to pings
    app.logger.info(worker)
    if worker.connection_status() != "Responding":
        warnings.append(WorkerWarning("Worker not responding to pings.",  
            "Please check the worker container and restart if necessary."))
    # TODO - Warning for fullnode without a working key
    # TODO - Warning for farmer too slow on pool partials: "Error in pooling: (2, 'The partial is too late."
    # TODO - Warning for harvester not connected (worker but not in farm summary)
    # TODO - Warning for harvester not responding quickly enough - 
    # TODO - Warning for harvester not responding often enough
    # TODO - Warning for plotter disk usage too high?
    # TODO - Warning if any blockchain challenges are higher than 5 seconds (show both hostname AND drive)
    # TODO - Warning if any blockchain challenges are missing in last hour (some percentage like that chart)
    # TODO - Warning if worker's Machinaris version does not match that of the fullnode
    # TODO - Warning if worker's time drifts more than 3 minutes off fullnode's WHEN responding with ping seconds ago
    return warnings
