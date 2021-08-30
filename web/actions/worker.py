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
    query = db.session.query(w.Worker).order_by(w.Worker.hostname)
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

def plot_count_from_summary(orig_hostname, worker_plot_file_count):
    app.logger.info("Searching for warnings on: {0}.".format(orig_hostname))
    try:
        hostname = socket.gethostbyname(orig_hostname)
    except Exception as ex:
        app.logger.info("Can't resolve original hostname: {0}".format(orig_hostname))
    try:    
        harvesters = asyncio.run(chia.load_plots_per_harvester())
        #app.logger.info(harvesters.keys())
        if hostname in harvesters:
            app.logger.info("Found hostname match for {0}".format(hostname))
            return len(harvesters[hostname])
        else:
            for harvester in harvesters:
                #app.logger.info("Harvester {0} has count: {1}".format(harvester, harvesters[harvester]))
                if worker_plot_file_count == len(harvesters[harvester]):
                    app.logger.info("No hostname match for {0} but found matching counts {1}".format(hostname, worker_plot_file_count))
                    return len(harvesters[harvester])
    except Exception as ex:
        app.logger.info("Failed to get harvester plot count for {0} due to {1}.".format(hostname, str(ex)))
    app.logger.info("Failed to find any match for hostname {0}".format(hostname))
    return None

def generate_warnings(worker, plots):
    warnings = []
    worker_plot_file_count = len(plots.rows)
    worker_summary_plot_count = plot_count_from_summary(worker.hostname, worker_plot_file_count)
    if not worker_summary_plot_count and worker_plot_file_count > 0:
        warnings.append(WorkerWarning("Disconnected harvester!", 
        "Farm summary reports no harvester for {0}, but Machinaris found {1} plots on disk. Further <a href='https://github.com/guydavis/machinaris/wiki/FAQ#farming-summary-and-file-listing-report-different-plot-counts' target='_blank' class='text-white'>investigation of the worker harvesting service</a> is recommended.".format(
            worker.hostname, worker_plot_file_count)))
    elif abs(worker_summary_plot_count - worker_plot_file_count) > 2:
        warnings.append(WorkerWarning("Mismatched plot counts!", 
        "Farm summary reports {0} plots for {1}, but Machinaris found {2} plots on disk. Further <a href='https://github.com/guydavis/machinaris/wiki/FAQ#farming-summary-and-file-listing-report-different-plot-counts' target='_blank' class='text-white'>investigation of the worker harvesting service</a> is recommended.".format(
            worker_summary_plot_count, worker.hostname, worker_plot_file_count)))
    return warnings
