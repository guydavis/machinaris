#
#
#

import datetime

from flask import Flask, jsonify, abort, request
from subprocess import Popen, TimeoutExpired, PIPE
from app.models import plotman
from app import app

PLOTMAN_SCRIPT = '/chia-blockchain/venv/bin/plotman'

RELOAD_MINIMUM_SECS = 30 # Don't query plotman unless at least this long since last time.

last_plotting_summary = None 
last_plotting_summary_load_time = None 

def load_plotting_summary():
    global last_plotting_summary
    global last_plotting_summary_load_time
    if last_plotting_summary and last_plotting_summary_load_time >= \
            (datetime.datetime.now() - datetime.timedelta(seconds=RELOAD_MINIMUM_SECS)):
        return last_plotting_summary

    proc = Popen("{0} status < /dev/tty".format(PLOTMAN_SCRIPT), stdout=PIPE, stderr=PIPE, shell=True)
    try:
        outs, errs = proc.communicate(timeout=10)
    except TimeoutExpired:
        proc.kill()
        abort(500, description="The timeout is expired!")
    if errs:
        app.logger.info(errs.decode('utf-8'))
        abort(500, description=errs.decode('utf-8'))
    
    last_plotting_summary = plotman.PlottingSummary(outs.decode('utf-8').splitlines())
    last_plotting_summary_load_time = datetime.datetime.now()
    return last_plotting_summary