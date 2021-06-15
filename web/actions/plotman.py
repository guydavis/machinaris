#
# CLI interactions with the plotman script.
#

import datetime
import os
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
    app.logger.info("Starting Plotman run....")
    try:
        utils.send_post(plotter, "/actions/", {"service": "plotting","action": "start"}, debug=True)
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
            utils.send_post(plotter, "/actions/", debug=True,
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
                hostname = plot['plotter']
        if hostname:
            if not hostname in plots_by_worker:
                plots_by_worker[hostname] = []
            plots_by_worker[hostname].append(plot_id)
    return plots_by_worker

def stop_plotman(plotter):
    app.logger.info("Stopping Plotman run....")
    try:
        utils.send_post(plotter, "/actions/", payload={"service": "plotting","action": "stop"}, debug=True)
    except:
        app.logger.info(traceback.format_exc())
        flash('Failed to stop Plotman plotting run!', 'danger')
        flash('Please see /root/.chia/plotman/logs/plotman.log', 'warning')
    else:
        flash('Plotman stopped successfully.  No new plots will be started, but existing ones will continue on.', 'success')

def start_archiving(plotter):
    app.logger.info("Starting Archiver....")
    try:
        utils.send_post(plotter, "/actions/", {"service": "archiving","action": "start"}, debug=True)
    except:
        app.logger.info(traceback.format_exc())
        flash('Failed to start Plotman archiver!', 'danger')
        flash('Please see log files.', 'warning')
    else:
        flash('Archiver started successfully.', 'success')

def stop_archiving(plotter):
    app.logger.info("Stopping Archiver run....")
    try:
        utils.send_post(plotter, "/actions/", payload={"service": "archiving","action": "stop"}, debug=True)
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
        utils.send_put(plotter, "/configs/plotting", config, debug=True)
    except Exception as ex:
        flash('Failed to save config to plotter.  Please check log files.', 'danger')
        flash(str(ex), 'warning')
    else:
        flash('Nice! Plotman\'s plotman.yaml validated and saved successfully.', 'success')

def find_plotting_job_log(plot_id):
    dir_path = '/root/.chia/plotman/logs'
    directory = os.fsencode(dir_path)
    for file in os.listdir(directory):
        filename = os.fsdecode(file)
        if filename.endswith(".log") and not filename.startswith('plotman.'): 
            with open(os.path.join(str(dir_path), filename)) as logfile:
                head = [next(logfile) for x in range(10)] # Check first 10 lines
                for line in head:
                    if plot_id in line:
                        return os.path.join(str(dir_path), filename)
            continue
        else:
            continue
    return None

def analyze(plot_file):
    groups = re.match("plot-k(\d+)-(\d+)-(\d+)-(\d+)-(\d+)-(\d+)-(\w+).plot", plot_file)
    if not groups:
        return "Invalid plot file name provided: {0}".format(plot_file)
    plot_log_file = find_plotting_job_log(groups[7])
    if plot_log_file:
        proc = Popen("{0} {1} {2} < /dev/tty".format(
            PLOTMAN_SCRIPT,'analyze', plot_log_file), stdout=PIPE, stderr=PIPE, shell=True)
        try:
            outs, errs = proc.communicate(timeout=90)
        except TimeoutExpired:
            proc.kill()
            proc.communicate()
            abort(500, description="The timeout is expired!")
        if errs:
            app.logger.error(errs.decode('utf-8'))
            return "Failed to analyze plot log.  See machinaris/logs/webui.log for details."
        return outs.decode('utf-8')
    return "Sorry, not plotting job log found.  Perhaps plot was made elsewhere?"
