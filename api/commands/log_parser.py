#
# Methods around reading and parsing service logs
#


import datetime
import itertools
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

from common.config import globals
from api.models import log
from api import app

# Rough number of challenges arriving per minute on a blockchain
CHALLENGES_PER_MINUTE = 8 

# Most recent partial proofs, actually double as 2 log lines per partial
PARTIALS_TO_LOAD = 50

# When reading tail of a log, only send this many lines
MAX_LOG_LINES = 250

def recent_challenges(blockchain):
    try:
        schedule_every_x_minutes = app.config['STATUS_EVERY_X_MINUTES']
        CHALLENGES_TO_LOAD = CHALLENGES_PER_MINUTE * int(schedule_every_x_minutes) + CHALLENGES_PER_MINUTE
    except:
        CHALLENGES_TO_LOAD = CHALLENGES_PER_MINUTE * 2 + CHALLENGES_PER_MINUTE
    log_file = get_farming_log_file(blockchain)
    if not os.path.exists(log_file):
        app.logger.debug(
            "Skipping challenges parsing as no such log file: {0}".format(log_file))
        return None
    proc = Popen("grep --text -i eligible {0} | tail -n {1}".format(log_file, CHALLENGES_TO_LOAD),
                 stdout=PIPE, stderr=PIPE, shell=True)
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
    #app.logger.debug("Challenges grep: {0}".format(cli_stdout))
    challenges = log.Challenges(cli_stdout.splitlines())
    # app.logger.debug(challenges)
    return challenges

def recent_partials(blockchain):
    log_file = get_farming_log_file(blockchain)
    if not os.path.exists(log_file):
        app.logger.debug(
            "Skipping partials parsing as no such log file: {0}".format(log_file))
        return []
    rotated_log_file = ''
    if os.path.exists(log_file + '.1'):
        rotated_log_file = log_file + '.1'
    proc = Popen("grep -h --text -C1 -i partial {0} {1} | tail -n {2}".format(rotated_log_file, log_file, PARTIALS_TO_LOAD),
                 stdout=PIPE, stderr=PIPE, shell=True)
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
    #app.logger.debug("Partials grep: {0}".format(cli_stdout))
    partials = log.Partials(cli_stdout.splitlines())
    # app.logger.debug(partials)
    return partials

def find_plotting_job_log(plot_id):
    dir_path = '/root/.chia/plotman/logs'
    directory = os.fsencode(dir_path)
    for file in os.listdir(directory):
        filename = os.fsdecode(file)
        try:
            if filename.endswith(".log") and not filename.startswith('plotman.'):
                with open(os.path.join(str(dir_path), filename)) as logfile:
                    for line in itertools.islice(logfile, 0, 20):
                        if plot_id in line:
                            return os.path.join(str(dir_path), filename)
                continue
            else:
                continue
        except:
            app.logger.info("find_plotting_job_log: Skipping error when reading head of {0}".format(filename))
            app.logger.info(traceback.format_exc())
    return None

def get_farming_log_file(blockchain):
    mainnet_folder = globals.get_blockchain_mainnet(blockchain)
    return mainnet_folder + '/log/debug.log'

def get_log_lines(log_type, log_id=None, blockchain=None):
    if log_type == "alerts":
        log_file = "/root/.chia/chiadog/logs/chiadog.log"
    elif log_type == "plotting":
        if log_id:
            log_file = find_plotting_job_log(log_id)
        else:
            log_file = "/root/.chia/plotman/logs/plotman.log"
    elif log_type == "archiving":
        log_file = "/root/.chia/plotman/logs/archiver.log"
    elif log_type == "farming":
        log_file= get_farming_log_file(blockchain)
    elif log_type == "webui":
        log_file = "/root/.chia/machinaris/logs/webui.log"
    elif log_type == "apisrv":
        log_file = "/root/.chia/machinaris/logs/apisrv.log"
    if not log_file or not os.path.exists(log_file):
        app.logger.info("No log file found at {0}".format(log_file))
        return 'No log file found!'
    #app.logger.info("Log file found at {0}".format(log_file))
    if blockchain == "chives":
        class_escape = re.compile(r' chives.plotting.(\w+)(\s+): ')
    elif blockchain == "flax":
        class_escape = re.compile(r' flax.plotting.(\w+)(\s+): ')
    elif blockchain == "flora":
        class_escape = re.compile(r' flora.plotting.(\w+)(\s+): ')
    elif blockchain == "hddcoin":
        class_escape = re.compile(r' hddcoin.plotting.(\w+)(\s+): ')
    else: # Chia and NChain both
        class_escape = re.compile(r' chia.plotting.(\w+)(\s+): ')
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    proc = Popen(['tail', '-n', str(MAX_LOG_LINES), log_file], stdout=PIPE)
    return class_escape.sub('', ansi_escape.sub('', proc.stdout.read().decode("utf-8")))
