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

from api.models import log
from api import app

# Location of the auto-rotating log in container
CHIA_LOG = '/root/.chia/mainnet/log/debug.log'

# Roughly 1 minutes worth of challenges
CHALLENGES_TO_LOAD = 8

# When reading tail of a log, only send this many lines
MAX_LOG_LINES = 250


def recent_challenges():
    if not os.path.exists(CHIA_LOG):
        app.logger.debug(
            "Skipping challenges parsing as no such log file: {0}".format(CHIA_LOG))
        return []
    proc = Popen("grep -i eligible {0} | tail -n {1}".format(CHIA_LOG, CHALLENGES_TO_LOAD),
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


def get_log_lines(log_type, log_id=None):
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
        log_file = "/root/.chia/mainnet/log/debug.log"
    if not log_file or not os.path.exists(log_file):
        app.logger.info("No log file found at {0}".format(log_file))
        return 'No log file found!'
    class_escape = re.compile(r' chia.plotting.(\w+)(\s+): ')
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    proc = Popen(['tail', '-n', str(MAX_LOG_LINES), log_file], stdout=PIPE)
    return class_escape.sub('', ansi_escape.sub('', proc.stdout.read().decode("utf-8")))
