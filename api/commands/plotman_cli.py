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
from api.models import plotman
from api import app

PLOTMAN_SCRIPT = '/chia-blockchain/venv/bin/plotman'

# Don't query plotman unless at least this long since last time.
RELOAD_MINIMUM_SECS = 30

last_plotting_summary = None
last_plotting_summary_load_time = None

def load_plotting_summary():
    global last_plotting_summary
    global last_plotting_summary_load_time
    if last_plotting_summary and last_plotting_summary_load_time >= \
            (datetime.datetime.now() - datetime.timedelta(seconds=RELOAD_MINIMUM_SECS)):
        return last_plotting_summary
    proc = Popen("{0} {1}".format(PLOTMAN_SCRIPT,
                 'status'), stdout=PIPE, stderr=PIPE, shell=True)
    try:
        outs, errs = proc.communicate(timeout=90)
    except TimeoutExpired:
        proc.kill()
        proc.communicate()
        abort(500, description="The timeout is expired!")
    if errs:
        app.logger.error(errs.decode('utf-8'))
        abort(500, description=errs.decode('utf-8'))
    cli_stdout = outs.decode('utf-8')
    #app.logger.info("Here is: {0}".format(cli_stdout))
    last_plotting_summary = plotman.PlottingSummary(
        cli_stdout.splitlines(), get_plotman_pid())
    last_plotting_summary_load_time = datetime.datetime.now()
    return last_plotting_summary

def dispatch_action(job):
    service = job['service']
    if service != 'plotting':
        raise Exception("Only plotting jobs handled here!")
    action = job['action']
    if action == "start":
        start_plotman()
    elif action == "stop":
        stop_plotman()
    elif action == "restart":
        stop_plotman()
        time.sleep(5)
        start_plotman()
    else:
        action_plots(job)

def action_plots(job):
    global last_plotting_summary
    app.logger.info("Actioning plots....")
    action = job['action']
    plot_ids = job['plot_ids']
    app.logger.info("About to {0} plots: {1}".format(action, plot_ids))
    for plot_id in plot_ids:
        try:
            prefix = ""
            if action == "kill":
                prefix = "printf 'y\n' |"
            logfile = "/root/.chia/plotman/logs/plotman.log"
            log_fd = os.open(logfile, os.O_RDWR | os.O_CREAT)
            log_fo = os.fdopen(log_fd, "a+")
            proc = Popen("{0} {1} {2} {3}".format(prefix, PLOTMAN_SCRIPT, action, plot_id),
                         shell=True, universal_newlines=True, stdout=log_fo, stderr=log_fo)
        except:
            app.logger.info('Failed to {0} selected plot {1}.'.format(action, plot_id))
            app.logger.info(traceback.format_exc())
            return

def get_plotman_pid():
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        if proc.info['name'] == 'plotman' and 'plot' in proc.info['cmdline']:
            return proc.info['pid']
    return None

def start_plotman():
    app.logger.info("Starting Plotman run...")
    try:
        logfile = "/root/.chia/plotman/logs/plotman.log"
        log_fd = os.open(logfile, os.O_RDWR | os.O_CREAT)
        log_fo = os.fdopen(log_fd, "a+")
        # TODO Figure out how to avoid need for tty here...
        proc = Popen("{0} {1} </dev/tty".format(PLOTMAN_SCRIPT, 'plot'),
                     shell=True, universal_newlines=True, stdout=log_fo, stderr=log_fo)
    except:
        app.logger.info('Failed to start Plotman plotting run!')
        app.logger.info(traceback.format_exc())
    else:
        # TODO Trigger an immediate status_plotman update.
        pass

def stop_plotman():
    app.logger.info("Stopping Plotman run...")
    try:
        os.kill(get_plotman_pid(), signal.SIGTERM)
    except:
        app.logger.info('Failed to stop Plotman plotting run!')
        app.logger.info(traceback.format_exc())
    else:
        # TODO Trigger an immediate status_plotman update. 
        pass

def get_archiver_pid():
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        if proc.info['name'] == 'plotman' and 'archive' in proc.info['cmdline']:
            return proc.info['pid']
    return None

def start_archiver():
    app.logger.info("Starting Archiver run...")
    try:
        logfile = "/root/.chia/plotman/logs/archiver.log"
        log_fd = os.open(logfile, os.O_RDWR | os.O_CREAT)
        log_fo = os.fdopen(log_fd, "a+")
        # TODO Figure out how to avoid need for tty here...
        proc = Popen("{0} {1} </dev/tty".format(PLOTMAN_SCRIPT, 'archive'),
                     shell=True, universal_newlines=True, stdout=log_fo, stderr=log_fo)
    except:
        app.logger.info('Failed to start Plotman archiving run!')
        app.logger.info(traceback.format_exc())
    else:
        # TODO Trigger an immediate status_plotman update.
        pass

def stop_archiver():
    app.logger.info("Stopping Archiver run...")
    try:
        os.kill(get_plotman_pid(), signal.SIGTERM)
    except:
        app.logger.info('Failed to stop Plotman archiving run!')
        app.logger.info(traceback.format_exc())
    else:
        # TODO Trigger an immediate status_plotman update. 
        pass

def load_config():
    return open('/root/.chia/plotman/plotman.yaml','r').read()

def save_config(config):
    try:
        # Validate the YAML first
        yaml.safe_load(config)
        # Save a copy of the old config file
        src = "/root/.chia/plotman/plotman.yaml"
        dst = "/root/.chia/plotman/plotman." + \
            time.strftime("%Y%m%d-%H%M%S")+".yaml"
        shutil.copy(src, dst)
        # Now save the new contents to main config file
        with open(src, 'w') as writer:
            writer.write(config)
    except Exception as ex:
        app.logger.info(traceback.format_exc())
        raise Exception('Updated plotman.yaml failed validation!\n' + str(ex))
    else:
        # TODO Restart plotman loop if running locally
        pass

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
        proc = Popen("{0} {1} {2}".format(
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
