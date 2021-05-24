#
# Methods around reading and parsing service logs
# 


import datetime
import os
import psutil
import signal
import shutil
import time
import traceback
import yaml

from flask import Flask, jsonify, abort, request, flash
from subprocess import Popen, TimeoutExpired, PIPE

from app.models import log
from app import app

# Location of the auto-rotating log in container
CHIA_LOG = '/root/.chia/mainnet/log/debug.log'

CHALLENGES_TO_LOAD = 5

MAX_LOG_LINES = 250

def recent_challenges():
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
    app.logger.info("Here is: {0}".format(cli_stdout))
    challenges = log.Challenges(cli_stdout.splitlines())
    app.logger.info(challenges)
    return challenges

def get_log_lines(log_type):
    if log_type == "alerts":
        log_file = "/root/.chia/chiadog/logs/chiadog.log"
    elif log_type == "plotting":
        log_file = "/root/.chia/plotman/logs/plotman.log"
    elif log_type == "farming":
        log_file = "/root/.chia/mainnet/log/debug.log"
    proc = Popen(['tail', '-n', str(MAX_LOG_LINES), log_file], stdout=PIPE)
    return proc.stdout.read()
