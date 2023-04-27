#
# CLI interactions with the plotman script.
#

import datetime
import glob
import itertools
import json
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
PLOTTING_SCHEDULES = '/root/.chia/machinaris/config/plotting_schedules.json'

# Don't query plotman unless at least this long since last time.
RELOAD_MINIMUM_SECS = 30

# Only load this many recent transfer log files, ignore older ones
NUM_RECENT_TRANSFER_LOGS = 25

def check_plotter(plotter_path):
    if not os.path.exists(plotter_path):
        raise Exception("Plotter not yet built at {0}. Please allow 15 minutes for startup.".format(plotter_path))

def check_config():
    if not os.path.exists(PLOTMAN_CONFIG):
        app.logger.info("No existing plotman config found, so copying sample to: {0}" \
                .format(PLOTMAN_CONFIG))
        shutil.copy(PLOTMAN_SAMPLE, PLOTMAN_CONFIG)
    with open(PLOTMAN_CONFIG) as f:
        config = yaml.safe_load(f)
        if 'plotting' in config:
            if 'type' in config['plotting']:
                if config['plotting']['type'] == 'madmax':
                    check_plotter('/usr/bin/chia_plot')
                elif config['plotting']['type'] == 'bladebit':
                    check_plotter('/usr/bin/bladebit')
                # Chia/Chives default plotters are built-into the image itself.

def check_script():
    if not os.path.exists(PLOTMAN_SCRIPT):
        return False
    return True

def load_plotting_summary():
    if not check_script():
        raise Exception("No plotman script found yet at {0}. Container probably just launched. Please allow 15 minutes for startup." \
                .format(PLOTMAN_SCRIPT))
    check_config()
    proc = Popen("{0} {1}".format(PLOTMAN_SCRIPT,
                 'status'), stdout=PIPE, stderr=PIPE, shell=True)
    try:
        outs, errs = proc.communicate(timeout=90)
        if errs:
            raise Exception("Errors during plotman status:\n {0}".format(errs.decode('utf-8')))
    except TimeoutExpired:
        proc.kill()
        proc.communicate()
        raise Exception("The timeout expired during plotman status.")
    cli_stdout = outs.decode('utf-8')
    return plotman.PlottingSummary(cli_stdout.splitlines(), get_plotman_pid())

def load_archiving_summary():
    # First collect any running rsync processes to see if transfer(s) are still in progress
    rsync_processes = []
    for process in psutil.process_iter():
        cmdline = process.cmdline()
        if cmdline and (len(cmdline) > 0) and cmdline[0] == 'rsync' and '--info=progress2' in cmdline:
            app.logger.info("Found running rsync transfer: {0} {1}".format(process.pid, cmdline))
            rsync_processes.append(process)
    # Then load most recent transfers (running and not) from archiving log folder
    transfers = []
    for transfer_log in sorted(glob.iglob('/root/.chia/plotman/logs/archiving/*.transfer.log'), key=os.path.getctime, reverse=True)[:NUM_RECENT_TRANSFER_LOGS]:
        transfer = plotman.Transfer(transfer_log, rsync_processes)
        if transfer and transfer.log_file:
            transfers.append(transfer)
    return transfers

def dispatch_action(job):
    if not check_script():
        raise Exception("No plotman script found yet at {0}. Container probably just launched. Please allow 15 minutes for startup." \
                .format(PLOTMAN_SCRIPT))
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
            param = ""
            if action == "kill":
                param = "--force"
            logfile = "/root/.chia/plotman/logs/plotman.log"
            log_fd = os.open(logfile, os.O_RDWR | os.O_CREAT)
            log_fo = os.fdopen(log_fd, "a+")
            proc = Popen("{0} {1} {2} {3}".format(PLOTMAN_SCRIPT, action, param, plot_id),
                         shell=True, universal_newlines=True, stdout=log_fo, stderr=log_fo)
            # Plotman regressed on cleaning temp after kill so do it here:
            clean_tmp_dirs_after_kill(plot_id)
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
    pid = get_plotman_pid()
    if pid:
        app.logger.error("Not starting Plotman as already running with PID: {0}".format(pid))
        return
    app.logger.info("Starting Plotman run...")
    check_config()
    if len(load_plotting_summary().rows) == 0:  # No plots running
        clean_tmp_dirs_before_run()  
    logfile = "/root/.chia/plotman/logs/plotman.log"
    fd_env = os.environ.copy()
    fd_env["PYTHONUNBUFFERED"] = "TRUE"  # Added to force Plotman to log properly
    proc = Popen("nohup {0} {1} >> {2} 2>&1 &".format(PLOTMAN_SCRIPT, 'plot', logfile),
                    env=fd_env, shell=True, stdin=DEVNULL, stdout=None, stderr=None, close_fds=True)
    app.logger.info("Completed launch of plotman.")

def clean_tmp_dirs_before_run():
    try:
        with open("/root/.chia/plotman/plotman.yaml") as f:
            config = yaml.safe_load(f)
            if 'directories' in config:
                if 'tmp' in config['directories']:
                    for tmp_dir in config['directories']['tmp']:
                        app.logger.info("No running plot jobs found so deleting {0}/*.tmp before starting plotman.".format(tmp_dir))
                        for p in pathlib.Path(tmp_dir).glob("*.tmp"):
                            p.unlink()
                if 'tmp2' in config['directories']:
                    tmp_dir = config['directories']['tmp2']
                    app.logger.info("No running plot jobs found so deleting {0}/*.tmp before starting plotman.".format(tmp_dir))
                    for p in pathlib.Path(tmp_dir).glob("*.tmp"):
                        p.unlink()
    except Exception as ex:
        app.logger.info("Skipping deletion of temp files due to {0}.".format(traceback.format_exc()))

def clean_tmp_dirs_after_kill(plot_id):
    try:
        with open("/root/.chia/plotman/plotman.yaml") as f:
            config = yaml.safe_load(f)
            if 'directories' in config:
                if 'tmp' in config['directories']:
                    for tmp_dir in config['directories']['tmp']:
                        for p in pathlib.Path(tmp_dir).glob("*{0}*.tmp".format(plot_id)):
                            app.logger.info("After kill, deleting stale tmp file: {0}".format(p))
                            p.unlink()
                if 'tmp2' in config['directories']:
                    tmp_dir = config['directories']['tmp2']
                    for p in pathlib.Path(tmp_dir).glob("*{0}*.tmp".format(plot_id)):
                        app.logger.info("After kill, deleting stale tmp file: {0}".format(p))
                        p.unlink()
    except Exception as ex:
        app.logger.info("Skipping deletion of temp files due to {0}.".format(traceback.format_exc()))

def stop_plotman():
    pid = get_plotman_pid()
    if not pid:
        app.logger.error("No need to stop Plotman as not currently running.")
        return
    app.logger.info("Stopping Plotman run...")
    os.kill(pid, signal.SIGTERM)

def get_archiver_pid():
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        if proc.info['name'] == 'plotman' and 'archive' in proc.info['cmdline']:
            return proc.info['pid']
    return None

def start_archiver():
    app.logger.info("Starting archiver run...")
    check_config()
    logfile = "/root/.chia/plotman/logs/archiver.log"
    app.logger.info("About to start archiver...")
    fd_env = os.environ.copy()
    fd_env["PYTHONUNBUFFERED"] = "TRUE"  # Added to force Plotman to log properly
    proc = Popen("nohup {0} {1} >{2} 2>&1 &".format(PLOTMAN_SCRIPT, 'archive', logfile),
                    env=fd_env, shell=True, stdin=DEVNULL, stdout=None, stderr=None, close_fds=True)
    app.logger.info("Completed launch of archiver.")

def stop_archiver():
    app.logger.info("Stopping Archiver run...")
    os.kill(get_archiver_pid(), signal.SIGTERM)

def load_config(blockchain):
    return open('/root/.chia/plotman/plotman.yaml','r').read()

def save_config(config, blockchain):
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
    # Now try to validate config by calling plotman status
    load_plotting_summary()
    # Finally restart plotman and archiver if they are running
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
            if filename.endswith(".log") and not filename.startswith('plotman.') and not filename.startswith('archiver.'):
                with open(os.path.join(str(dir_path), filename)) as logfile:
                    for line in itertools.islice(logfile, 0, 50):
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
    groups = re.match("plot(?:-mmx)?-k(\d+)(?:-c\d+)?-(\d+)-(\d+)-(\d+)-(\d+)-(\d+)-(\w+).plot", plot_file)
    if not groups:
        return "Invalid plot file name provided: {0}".format(plot_file)
    plot_log_file = find_plotting_job_log(groups[7])
    if plot_log_file:
        proc = Popen("{0} {1} {2}".format(
            PLOTMAN_SCRIPT,'analyze', plot_log_file), stdout=PIPE, stderr=PIPE, shell=True)
        try:
            outs, errs = proc.communicate(timeout=90)
            if errs:
                app.logger.error(errs.decode('utf-8'))
                raise Exception("Failed to analyze plot.")
        except TimeoutExpired:
            proc.kill()
            proc.communicate()
            raise Exception("The timeout is expired attempting to start plot analyze.")
        return outs.decode('utf-8')
    return None

def get_prometheus_metrics():
    check_config()
    proc = Popen("{0} {1}".format(PLOTMAN_SCRIPT,
                 'prometheus'), stdout=PIPE, stderr=PIPE, shell=True)
    try:
        outs, errs = proc.communicate(timeout=90)
        if errs:
            raise Exception("Errors during plotman call:\n {0}".format(errs.decode('utf-8')))
    except TimeoutExpired:
        proc.kill()
        proc.communicate()
        raise Exception("The timeout expired during plotman call.")
    cli_stdout = outs.decode('utf-8')
    return cli_stdout

def load_dirs(blockchain):
    if not check_script():
        raise Exception("No plotman script found yet at {0}. Container probably just launched. Please allow 15 minutes for startup." \
                .format(PLOTMAN_SCRIPT))
    check_config()
    proc = Popen("{0} {1} {2}".format(PLOTMAN_SCRIPT, 'dirs', '--json'), stdout=PIPE, stderr=PIPE, shell=True)
    try:
        outs, errs = proc.communicate(timeout=90)
    except TimeoutExpired:
        proc.kill()
        proc.communicate()
        raise Exception("The timeout expired during plotman dirs.")
    result = {}
    try:
        response = json.loads(outs.decode('utf-8'))
        if not 'temporary' in response:
            response['temporary'] = []
        if not 'destination' in response:
            response['destination'] = []
        if not 'archiving' in response:
            response['archiving'] = []
    except:
        response = outs.decode('utf-8')
    result = {'response': response, }
    if errs.decode('utf-8'):
        result['errors'] = errs.decode('utf-8')
    return json.dumps(result)

def load_schedule():
    if os.path.exists(PLOTTING_SCHEDULES):
        try:
            return json.dumps(json.loads(open(PLOTTING_SCHEDULES,'r').read()))
        except Exception as ex:
            app.logger.error("Failed to read plotting schedule from {0} due to {1}.".format(PLOTTING_SCHEDULES, str(ex)))
    return [] # Return an empty schedule response if not present.

# A reference to the scheduler
saved_scheduler = None

def save_schedule(schedule):
    global saved_scheduler
    with open(PLOTTING_SCHEDULES, 'w') as writer:
        writer.write(schedule)
    if saved_scheduler:
        schedule_plotting(saved_scheduler)
    app.logger.info("Saved updated plotting schedule to {0}.".format(PLOTTING_SCHEDULES))

# Invoked on launch of the API app when it creates the scheduler
def schedule_plotting(scheduler):
    global saved_scheduler
    if scheduler:
        saved_scheduler = scheduler
    for job in scheduler.get_jobs():
        app.logger.debug("JOB NAME: {0}".format(job.name))
        if job.name in ['scheduled_start_plotman', 'scheduled_stop_plotman']:
            app.logger.info("Removing previously scheduled job {0}".format(job.id))
            job.remove()
    try:
        schedules = json.loads(load_schedule())
        for schedule in schedules:
            app.logger.info("Scheduling plotting with schedule: {0}".format(schedule))
            start = schedule['start'].split(' ')
            if len(start) == 5:
                scheduler.add_job(func=start_plotman, name="scheduled_start_plotman", trigger='cron', minute=start[0], hour=start[1], day=start[2], month=start[3], day_of_week=start[4])
            else:
                app.logger.error("Skipped stop of plotting for malformed schedule cron: {0}")
            stop = schedule['stop'].split(' ')
            if len(stop) == 5:
                scheduler.add_job(func=stop_plotman, name="scheduled_stop_plotman", trigger='cron', minute=stop[0], hour=stop[1], day=stop[2], month=stop[3], day_of_week=stop[4])
            else:
                app.logger.error("Skipped stop of plotting for malformed schedule cron: {0}")
    except Exception as ex:
        app.logger.error("Error when scheduling plotman: {0}".format(str(ex)))
