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
from flask_babel import _, lazy_gettext as _l

from web import app, db, utils
from common.config import globals
from common.models import alerts, blockchains, challenges, connections, farms, \
    keys, plots, plottings, plotnfts, pools, wallets, workers
from web.models.worker import WorkerSummary, WorkerWarning
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
        app.logger.debug("{0} -> {1}".format(worker.blockchain, worker.hostname))
    return fullnodes

def default_blockchain():
    first_blockchain = None
    for worker in db.session.query(workers.Worker).filter(workers.Worker.mode=='fullnode').order_by(workers.Worker.blockchain).all():
        if not first_blockchain:
            first_blockchain = worker.blockchain
        if worker.blockchain == 'chia':  # Default choice
            return worker.blockchain
        if worker.blockchain == 'chives':  # Second choice
            return worker.blockchain
    return first_blockchain # Last choice, just use whatever is first alphabetically

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

# Often users set different timezones for workers, leading to hours of local time difference
def check_worker_time_near_to_controller(worker):
    try:
        worker_time = datetime.datetime.strptime(worker.time_on_worker, "%Y-%m-%d %H:%M:%S")
        if abs((worker_time - datetime.datetime.now()).total_seconds()) > (60 * 10):
            return True
    except:
        traceback.print_exc()
    return False

def generate_warnings(worker):
    warnings = []
    # Check if worker is responding to pings
    if worker.connection_status() != "Responding":
        warnings.append(WorkerWarning(_("Worker not responding to pings."),  
            _("Please check the worker container and restart if necessary."), 'error'))
    elif check_worker_time_near_to_controller(worker):
        warnings.append(WorkerWarning(_("Worker time is offset from controller."),  
            _("Please ensure worker and controller share same timezone."), 'warning'))
    worker_version = worker.machinaris_version()
    controller_version = globals.load_machinaris_version()
    if worker_version != controller_version:
        app.logger.info('Worker {0}:{1} for {2} has version {3}, but controller version is {4}.'.format(
            worker.hostname, worker.port, worker.blockchain, worker_version, controller_version))
        warnings.append(WorkerWarning(_("Machinaris version does not match controller."),  
            _("Please use a consistent Machinaris version to avoid issues."), 'warning'))

    # TODO - Warning for fullnode without a working key
    # TODO - Warning for farmer too slow on pool partials: "Error in pooling: (2, 'The partial is too late."
    # TODO - Warning for harvester not connected (worker but not in farm summary)
    # TODO - Warning for harvester not responding quickly enough - 
    # TODO - Warning for harvester not responding often enough
    # TODO - Warning for plotter disk usage too high?
    # TODO - Warning if any blockchain challenges are higher than 5 seconds (show both hostname AND drive)
    # TODO - Warning if any blockchain challenges are missing in last hour (some percentage like that chart)
    # TODO - Warning if worker's time drifts more than 3 minutes off fullnode's WHEN responding with ping seconds ago
    # TODO - Warning if farmer sync status falls behind while running (at 5 mins, before a later restart is attempted)
    # TODO - Warning if fullnode/harvester is not reporting disk stats
    return warnings