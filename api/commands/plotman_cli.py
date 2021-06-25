#
# CLI interactions with the plotman script.
#

import datetime
import itertools
import os
import pathlib
import psutil
import re
import signal
import shutil
import time
import traceback
import yaml

from flask import Flask, jsonify, abort, request, flash
from subprocess import Popen, TimeoutExpired, PIPE, DEVNULL
from api.models import plotman
from api import app

PLOTMAN_CONFIG = '/root/.chia/plotman/plotman.yaml'
PLOTMAN_SAMPLE = '/machinaris/config/plotman.sample.yaml'
PLOTMAN_SCRIPT = '/chia-blockchain/venv/bin/plotman'

# Don't query plotman unless at least this long since last time.
RELOAD_MINIMUM_SECS = 30

def check_config():
    if not os.path.exists(PLOTMAN_CONFIG):
        app.logger.info("No existing plotman config found, so copying sample to: {0}" \
                .format(PLOTMAN_CONFIG))
        shutil.copy(PLOTMAN_SAMPLE, PLOTMAN_CONFIG)

def load_plotting_summary():
    check_config()
    proc = Popen("{0} {1} < /dev/tty".format(PLOTMAN_SCRIPT,
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
    return plotman.PlottingSummary(cli_stdout.splitlines(), get_plotman_pid())

def dispatch_action(job):
    service = job['service']
    action = job['action']
    if service == 'plotting':
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
    elif service == 'archiving':
        if action == "start":
            start_archiver()
        elif action == "stop":
            stop_archiver()

def action_plots(job):
    check_config()
    #app.logger.info("Actioning plots....")
    action = job['action']
    plot_ids = job['plot_ids']
    #app.logger.info("About to {0} plots: {1}".format(action, plot_ids))
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
    check_config()
    try:
        if len(load_plotting_summary().rows) == 0:  # No plots running
            clean_tmp_dirs_before_run()  
        logfile = "/root/.chia/plotman/logs/plotman.log"
        proc = Popen("nohup {0} {1} < /dev/tty >> {2} 2>&1 &".format(PLOTMAN_SCRIPT, 'plot', logfile),
                     shell=True, stdin=DEVNULL, stdout=None, stderr=None, close_fds=True)
        app.logger.info("Completed launch of plotman.")
    except:
        app.logger.info('Failed to start Plotman plotting run!')
        app.logger.info(traceback.format_exc())

def clean_tmp_dirs_before_run():
    try:
        with open("/root/.chia/plotman/plotman.yaml") as f:
            config = yaml.safe_load(f)
            for tmp_dir in config['directories']['tmp']:
                app.logger.info("No running plot jobs found so deleting {0}/*.tmp before starting plotman.".format(tmp_dir))
                for p in pathlib.Path(tmp_dir).glob("*.tmp"):
                    p.unlink()
    except Exception as ex:
        app.logger.info(traceback.format_exc())
        raise Exception('Updated plotman.yaml failed validation!\n' + str(ex))

def stop_plotman():
    app.logger.info("Stopping Plotman run...")
    try:
        os.kill(get_plotman_pid(), signal.SIGTERM)
    except:
        app.logger.info('Failed to stop Plotman plotting run!')
        app.logger.info(traceback.format_exc())

def get_archiver_pid():
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        if proc.info['name'] == 'plotman' and 'archive' in proc.info['cmdline']:
            return proc.info['pid']
    return None

def start_archiver():
    app.logger.info("Starting archiver run...")
    check_config()
    try:
        logfile = "/root/.chia/plotman/logs/archiver.log"
        app.logger.info("About to start archiver...")
        proc = Popen("nohup {0} {1} < /dev/tty >> {2} 2>&1 &".format(PLOTMAN_SCRIPT, 'archive', logfile),
                     shell=True, stdin=DEVNULL, stdout=None, stderr=None, close_fds=True)
        app.logger.info("Completed launch of archiver.")
    except:
        app.logger.info('Failed to start Plotman archiving run!')
        app.logger.info(traceback.format_exc())

def stop_archiver():
    app.logger.info("Stopping Archiver run...")
    try:
        os.kill(get_archiver_pid(), signal.SIGTERM)
    except:
        app.logger.info('Failed to stop Plotman archiving run!')
        app.logger.info(traceback.format_exc())

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
    else: # Restart services if running
        if get_plotman_pid():
            stop_plotman()
            start_plotman()
        if get_archiver_pid():
            stop_archiver()
            start_archiver()

def find_plotting_job_log(plot_id):
    dir_path = '/root/.chia/plotman/logs'
    directory = os.fsencode(dir_path)
    for file in os.listdir(directory):
        filename = os.fsdecode(file)
        try:
            if filename.endswith(".log") and not filename.startswith('plotman.'):
                with open(os.path.join(str(dir_path), filename)) as logfile:
                    for line in itertools.islice(logfile, 0, 15):
                        if plot_id in line:
                            return os.path.join(str(dir_path), filename)
                continue
            else:
                continue
        except:
            app.logger.info("find_plotting_job_log: Skipping error when reading head of {0}".format(filename))
            app.logger.info(traceback.format_exc())
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
            abort(500, description="The timeout is expired attempting to start plots check.")
        if errs:
            app.logger.error(errs.decode('utf-8'))
            abort(500, description="Failed to analyze plots.")
        return outs.decode('utf-8')
    return None
