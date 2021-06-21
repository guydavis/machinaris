#
# CLI interactions with the plotman script.
#

import datetime
import os
from flask.helpers import make_response
import psutil
import re
import signal
import shutil
import time
import traceback
import yaml

from flask import Flask, jsonify, abort, request, flash
from subprocess import Popen, TimeoutExpired, PIPE
from common.models import plottings as pl
from web import app, db, utils
from web.models.plotman import PlottingSummary
from . import worker as w

PLOTMAN_SCRIPT = '/chia-blockchain/venv/bin/plotman'

# Don't query plotman unless at least this long since last time.
RELOAD_MINIMUM_SECS = 30

def load_plotting_summary():
    plottings = db.session.query(pl.Plotting).all()
    return PlottingSummary(plottings)

def load_plotters():
    plotters = []
    for plotter in w.load_worker_summary().plotters:
        plotters.append({
            'hostname': plotter.hostname,
            'plotting_status': plotter.plotting_status(),
            'archiving_status': plotter.archiving_status(),
            'archiving_enabled': plotter.archiving_enabled()
        })
    return plotters

def start_plotman(plotter):
    app.logger.info("Starting Plotman run...")
    try:
        utils.send_post(plotter, "/actions/", {"service": "plotting","action": "start"}, debug=False)
    except:
        app.logger.info(traceback.format_exc())
        flash('Failed to start Plotman plotting run!', 'danger')
        flash('Please see log files.', 'warning')
    else:
        flash('Plotman started successfully.', 'success')

def action_plots(action, plot_ids):
    plots_by_worker = group_plots_by_worker(plot_ids)
    app.logger.info("About to {0} plots: {1}".format(action, plots_by_worker))
    error = False
    for hostname in plots_by_worker.keys():
        try:
            plotter = w.get_worker_by_hostname(hostname)
            plot_ids = plots_by_worker[hostname]
            utils.send_post(plotter, "/actions/", debug=False,
                payload={"service": "plotting","action": action, "plot_ids": plot_ids}
            )
        except:
            error = True
            app.logger.info(traceback.format_exc())
    if error:
        flash('Failed to action all plots!', 'danger')
        flash('Please see the log file(s) on your plotter(s).', 'warning')
    else:
        flash('Plotman was able to {0} the selected plots successfully.'.format(
            action), 'success')

def group_plots_by_worker(plot_ids):
    plots_by_worker = {}
    all_plottings = load_plotting_summary()
    for plot_id in plot_ids:
        hostname = None
        for plot in all_plottings.rows:
            if plot['plot_id'] == plot_id:
                hostname = plot['worker']
        if hostname:
            if not hostname in plots_by_worker:
                plots_by_worker[hostname] = []
            plots_by_worker[hostname].append(plot_id)
    return plots_by_worker

def stop_plotman(plotter):
    app.logger.info("Stopping Plotman run...")
    try:
        utils.send_post(plotter, "/actions/", payload={"service": "plotting","action": "stop"}, debug=False)
    except:
        app.logger.info(traceback.format_exc())
        flash('Failed to stop Plotman plotting run!', 'danger')
        flash('Please see /root/.chia/plotman/logs/plotman.log', 'warning')
    else:
        flash('Plotman stopped successfully.  No new plots will be started, but existing ones will continue on.', 'success')

def start_archiving(plotter):
    app.logger.info("Starting Archiver....")
    try:
        utils.send_post(plotter, "/actions/", {"service": "archiving","action": "start"}, debug=False)
    except:
        app.logger.info(traceback.format_exc())
        flash('Failed to start Plotman archiver!', 'danger')
        flash('Please see log files.', 'warning')
    else:
        flash('Archiver started successfully.', 'success')

def stop_archiving(plotter):
    app.logger.info("Stopping Archiver run....")
    try:
        utils.send_post(plotter, "/actions/", payload={"service": "archiving","action": "stop"}, debug=False)
    except:
        app.logger.info(traceback.format_exc())
        flash('Failed to stop Plotman archiver', 'danger')
        flash('Please see /root/.chia/plotman/logs/archiver.log', 'warning')
    else:
        flash('Archiver stopped successfully.', 'success')

def load_config(plotter):
    return utils.send_get(plotter, "/configs/plotting", debug=False).content

def save_config(plotter, config):
    try: # Validate the YAML first
        yaml.safe_load(config)
    except Exception as ex:
        app.logger.info(traceback.format_exc())
        flash('Updated plotman.yaml failed validation! Fix and save or refresh page.', 'danger')
        flash(str(ex), 'warning')
    try:
        utils.send_put(plotter, "/configs/plotting", config, debug=False)
    except Exception as ex:
        flash('Failed to save config to plotter.  Please check log files.', 'danger')
        flash(str(ex), 'warning')
    else:
        flash('Nice! Plotman\'s plotman.yaml validated and saved successfully.', 'success')

def analyze(plot_file, plotters):
    # Don't know which plotter might have the plot result so try them in-turn
    for plotter in plotters:
        if plotter.latest_ping_result != "Responding":
            app.logger.info("Skipping analyze call to {0} as last ping was: {1}".format( \
                plotter.hostname, plotter.latest_ping_result))
            continue
        try:
            app.logger.info("Trying {0} for analyze....".format(plotter.hostname))
            payload = {"service":"plotting", "action":"analyze", "plot_file": plot_file }
            response = utils.send_post(plotter, "/analysis/", payload, debug=False)
            if response.status_code == 200:
                return response.content.decode('utf-8')
            elif response.status_code == 404:
                app.logger.info("Plotter on {0} did not have plot log for {1}".format(plotter.hostname, plot_file))
            else:
                app.logger.info("Plotter on {0} returned an unexpected error: {1}".format(plotter.hostname, response.status_code))
        except:
            app.logger.info(traceback.format_exc())
    return make_response("Sorry, not plotting job log found.  Perhaps plot was made elsewhere?", 200)