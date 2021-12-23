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

from sqlalchemy import or_
from flask import Flask, jsonify, abort, request, flash

from web import app, db, utils
from common.models import alerts, blockchains, challenges, connections, farms, \
    keys, plots, plottings, plotnfts, pools, wallets, workers
from web.models.worker import WorkerSummary
from web.actions import stats

ALL_TABLES_BY_HOSTNAME_AND_BLOCKCHAIN = [
    alerts.Alert,
    blockchains.Blockchain,
    challenges.Challenge,
    connections.Connection,
    farms.Farm, 
    keys.Key,
    plots.Plot,
    plottings.Plotting,
    plotnfts.Plotnft,
    pools.Pool,
    wallets.Wallet,
    workers.Worker
]

def load_worker_summary(hostname = None):
    query = db.session.query(workers.Worker).order_by(workers.Worker.displayname, workers.Worker.blockchain)
    if hostname:
        wkrs = query.filter(workers.Worker.hostname==hostname)
    else:
        wkrs = query.all()
    return WorkerSummary(wkrs)

def load_workers():
    return load_worker_summary().workers

def get_worker(hostname, blockchain='chia'):
    #app.logger.info("Searching for worker with hostname: {0} and blockchain: {1}".format(hostname, blockchain))
    return db.session.query(workers.Worker).filter(workers.Worker.hostname==hostname, workers.Worker.blockchain==blockchain).first()

def get_fullnode(blockchain='chia'):
    #app.logger.info("Searching for fullnode with blockchain: {0}".format(blockchain))
    return db.session.query(workers.Worker).filter(workers.Worker.mode=='fullnode', workers.Worker.blockchain==blockchain).first()

def get_fullnodes_by_blockchain():
    fullnodes = {}
    for worker in db.session.query(workers.Worker).filter(workers.Worker.mode=='fullnode').all():
        fullnodes[worker.blockchain] = worker
    return fullnodes

def prune_workers_status(workers):
    for id in workers:
        [hostname,blockchain] = id.split('|')
        worker = get_worker(hostname, blockchain)
        if worker:
            if 'chia' == blockchain:
                stats.prune_workers_status(hostname, worker.displayname, worker.blockchain)
            for table in ALL_TABLES_BY_HOSTNAME_AND_BLOCKCHAIN:
                db.session.query(table).filter(or_((table.hostname == hostname), (table.hostname == worker.displayname)), table.blockchain == worker.blockchain).delete()
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
