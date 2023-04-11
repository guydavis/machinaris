#
# If user has enabled replotting on the Farming page, then periodically
# check for old plots on farmers, meeting the provided criteria, to delete
# Only deletes a few plots at a time, there are guards to prevent deleting all
# Elsewhere, plotman will then see available disk space and plot a new plot into it.
#

import datetime
import json
import pathlib
import os
import sqlite3
import threading
import time
import traceback

from flask import g
from sqlalchemy import or_

from common.models import plots as p, plottings as pl
from common.models import workers as w
from common.config import globals
from api import app, utils

REPLOTTING_CONFIG = '/root/.chia/machinaris/config/replotting.json'

def load_replotting_settings():
    settings = {}
    if os.path.exists(REPLOTTING_CONFIG):
        with open(REPLOTTING_CONFIG, 'r') as fp:
            settings = json.loads(fp.read())
    return settings

def gather_harvesters(db, blockchain):
    workers = []
    query = db.session.query(p.Plot.hostname.distinct().label("hostname")).filter(p.Plot.blockchain == blockchain)
    for hostname in [row.hostname for row in query.all()]:
        worker = db.session.query(w.Worker).filter(w.Worker.blockchain == blockchain, w.Worker.hostname == hostname).first()
        if worker: 
            workers.append(worker)
        else:
            app.logger.error("Found no worker for {0} at {1}".format(blockchain, hostname))
    return workers

def gather_oldest_solo_plots(db, harvester):
    return db.session.query(p.Plot).filter(p.Plot.blockchain == harvester.blockchain, p.Plot.hostname == harvester.hostname,
        p.Plot.type == 'solo').order_by(p.Plot.created_at.asc()).limit(20).all()

def gather_plots_before(db, harvester, delete_before_date):
    return db.session.query(p.Plot).filter(p.Plot.blockchain == harvester.blockchain, p.Plot.hostname == harvester.hostname,
        p.Plot.created_at < "{0} 00:00".format(delete_before_date)).order_by(p.Plot.created_at.asc()).limit(20).all()

def gather_plots_by_ksize(db, harvester, delete_by_ksizes):
    if len(delete_by_ksizes) == 0:
        app.logger.error("Invalid empty list of ksizes to select plots for deletion.")
        return []
    for ksize in delete_by_ksizes:
        if not ksize in p.KSIZES:
            app.logger.error("Invalid target ksize for deletion provided: {0}".format(ksize))
            return []
    return db.session.query(p.Plot).filter(p.Plot.blockchain == harvester.blockchain, p.Plot.hostname == harvester.hostname,
        or_(*[p.Plot.file.like("%-k{0}-%".format(ksize)) for ksize in delete_by_ksizes])).order_by(p.Plot.created_at.asc()).limit(20).all()

def limit_deletes_to_accomodate_ksize(db, candidate_plots, free_ksize):
    size_bytes_to_delete = 0
    plots_to_delete = []
    try:
        required_free_space = p.FREE_GIBS_REQUIRED_FOR_KSIZE[free_ksize]
        for plot in candidate_plots:
            if size_bytes_to_delete >= (required_free_space * 1024 * 1024 * 1024):
                return plots_to_delete
            plots_to_delete.append(os.path.join(plot.dir, plot.file))
            size_bytes_to_delete += plot.size
    except Exception as ex:
        app.logger.error("Error limiting candidate plots to minimum required for k{0} size replotting because {1}".format(free_ksize, str(ex)))
    return plots_to_delete # Maybe empty if no candiate plots needed

def send_delete_request(harvester, blockchain, free_ksize, candidate_plots):
    app.logger.info("Requesting deletion of these plots on {0} ({1}) to allow replotting: {2}".format(harvester.displayname, harvester.hostname, candidate_plots))
    payload = {"service": "farming", "blockchain": blockchain, "action": "delete_for_replotting", "free_ksize": free_ksize, "plot_files": candidate_plots }
    try:
        utils.send_worker_post(harvester, "/actions/", payload=payload, debug=False)        
    except Exception as ex:
        app.logger.error('Failed request plot deletion for replotting from {0} ({1}) because {2}'.format(harvester.displayname, harvester.hostname, str(ex)))
    
def execute():
    with app.app_context():
        from api import db
        gc = globals.load()
        if not gc['is_controller']:
            return # Only controller should initiate a check for plots to delete, allowing replotting
        replotting_settings = load_replotting_settings()
        for blockchain in pl.PLOTTABLE_BLOCKCHAINS:
            if not blockchain in replotting_settings or not replotting_settings[blockchain]['enabled']:
                app.logger.info("Skipping check for plot deletion as replotting on {0} is disabled.".format(blockchain.capitalize()))
            else:
                try:
                    settings = replotting_settings[blockchain] # Work with settings for this blockchain in particular
                    for harvester in gather_harvesters(db, blockchain):
                        app.logger.debug("Checking {0} harvester {1} for candidate plot deletions. ({2})".format(blockchain, harvester.displayname, harvester.hostname))
                        candidate_plots = []
                        if settings['delete_solo']:
                            candidate_plots.extend(gather_oldest_solo_plots(db, harvester))
                        if settings['delete_before']:
                            candidate_plots.extend(gather_plots_before(db, harvester, settings['delete_before_date']))
                        if settings['delete_by_ksize']:
                            candidate_plots.extend(gather_plots_by_ksize(db, harvester, settings['delete_by_ksizes']))
                        if len(candidate_plots) > 0:
                            candidate_plots = limit_deletes_to_accomodate_ksize(db, candidate_plots, settings['free_ksize'])
                        if len(candidate_plots) > 0:
                            try:
                                thread = threading.Thread(target=send_delete_request, 
                                    kwargs={
                                        'harvester': harvester, 
                                        'blockchain': blockchain, 
                                        'free_ksize': settings['free_ksize'],
                                        'candidate_plots': candidate_plots
                                    }
                                )
                                thread.start()
                            except Exception as ex:
                                app.logger.info(traceback.format_exc())
                            #send_delete_request(harvester, blockchain, settings['free_ksize'], candidate_plots)
                        else:
                            app.logger.info("Found no candidate plots for {0} replotting on {1} ({2})".format(blockchain, harvester.displayname, harvester.hostname))
                except Exception as ex:
                    app.logger.error("Failed to check for candidate {0} replotting deletions because {1}".format(blockchain, str(ex)))
                    traceback.print_exc()