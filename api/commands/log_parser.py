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
from . import plotman_cli
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
    proc = Popen("grep --text -i eligible {0} | grep -v ': DEBUG' | tail -n {1}".format(log_file, CHALLENGES_TO_LOAD),
                 stdout=PIPE, stderr=PIPE, shell=True)
    try:
        outs, errs = proc.communicate(timeout=90)
        if errs:
            app.logger.error(errs.decode('utf-8'))
            return []
    except TimeoutExpired:
        proc.kill()
        proc.communicate()
        raise Exception("The timeout is expired!")
    cli_stdout = outs.decode('utf-8')
    #app.logger.debug("Challenges grep: {0}".format(cli_stdout))
    challenges = log.Challenges(cli_stdout.splitlines(), blockchain)
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
    proc = Popen("grep -h --text -i 'submitting partial' {0} {1} | tail -n {2}".format(rotated_log_file, log_file, PARTIALS_TO_LOAD),
                 stdout=PIPE, stderr=PIPE, shell=True)
    try:
        outs, errs = proc.communicate(timeout=90)
        if errs:
            app.logger.error(errs.decode('utf-8'))
            return []
    except TimeoutExpired:
        proc.kill()
        proc.communicate()
        raise Exception("The timeout is expired!")
    cli_stdout = outs.decode('utf-8')
    #app.logger.debug("Partials grep: {0}".format(cli_stdout))
    partials = log.Partials(cli_stdout.splitlines())
    # app.logger.debug(partials)
    return partials

def recent_farmed_blocks(blockchain):
    log_file = get_farming_log_file(blockchain)
    if not os.path.exists(log_file):
        app.logger.debug(
            "Skipping farmed blocks parsing as no such log file: {0}".format(log_file))
        return []
    rotated_log_file = ''
    if os.path.exists(log_file + '.1'):  # Only for Chia + fork blockchains
        rotated_log_file = log_file + '.1'
    if blockchain == 'mmx':
        #app.logger.info("MMX executing: grep 'Created block' {0}".format(log_file))
        proc = Popen("grep 'Created block' {0}".format(log_file), stdout=PIPE, stderr=PIPE, shell=True)
    else:
        # Chia 1.4+ sprays lots of useless "Cumulative cost" log lines right in middle of important lines, so ignore them
        proc = Popen("grep -v 'Cumulative cost' {0} {1} | grep -v 'CompressorArg' | grep -B 15 'Farmed unfinished_block'".format(rotated_log_file, log_file),
                 stdout=PIPE, stderr=PIPE, shell=True)
    try:
        outs, errs = proc.communicate(timeout=90)
        if errs:
            app.logger.error(errs.decode('utf-8'))
            return []
    except TimeoutExpired:
        proc.kill()
        proc.communicate()
        raise Exception("The timeout is expired!")
    cli_stdout = outs.decode('utf-8')
    #app.logger.info("Blocks grep: {0}".format(cli_stdout))
    blocks = log.Blocks(blockchain, cli_stdout.splitlines())
    #app.logger.info(blocks.rows)
    return blocks

def get_farming_log_file(blockchain):
    mainnet_folder = globals.get_blockchain_network_path(blockchain)
    if blockchain == 'mmx':
        return mainnet_folder + "/logs/mmx_node_{0}.txt".format(datetime.datetime.now().strftime("%Y_%m_%d"))
    return mainnet_folder + '/log/debug.log'

def get_log_lines(log_type, log_id=None, blockchain=None):
    if log_type == "alerts":
        log_file = "/root/.chia/chiadog/logs/chiadog.log"
    elif log_type == "plotting":
        if log_id:
            log_file = plotman_cli.find_plotting_job_log(log_id)
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
    elif log_type == "pooling":
        log_file = "/root/.chia/machinaris/logs/plotnft.log"
    elif log_type == "rewards":
        log_file = "/root/.chia/machinaris/logs/rewards.log"
    if not log_file or not os.path.exists(log_file):
        app.logger.info("No log file found at {0}".format(log_file))
        return 'No log file found!'
    #app.logger.info("Log file found at {0}".format(log_file))
    ansi_escape = re.compile(r'\x1B(?:[@A-Z\\-_]|\[[0-9:;<=>?]*[ -/]*[@-~])')
    proc = Popen(['tail', '-n', str(MAX_LOG_LINES), log_file], stdout=PIPE)
    return ansi_escape.sub('', proc.stdout.read().decode("utf-8"))
