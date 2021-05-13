#
# CLI interactions with the chia binary.
#

import datetime
import os.path

from flask import Flask, jsonify, abort, request
from subprocess import Popen, TimeoutExpired, PIPE
from os import path

from app.models import chia

CHIA_BINARY = '/chia-blockchain/venv/bin/chia'

RELOAD_MINIMUM_SECS = 30 # Don't query chia unless at least this long since last time.

last_farm_summary = None 
last_farm_summary_load_time = None 

def load_farm_summary():
    global last_farm_summary
    global last_farm_summary_load_time
    if last_farm_summary and last_farm_summary_load_time >= \
            (datetime.datetime.now() - datetime.timedelta(seconds=RELOAD_MINIMUM_SECS)):
        return last_farm_summary

    proc = Popen("{0} farm summary".format(CHIA_BINARY), stdout=PIPE, stderr=PIPE, shell=True)
    try:
        outs, errs = proc.communicate(timeout=25)
    except TimeoutExpired:
        proc.kill()
        abort(500, description="The timeout is expired!")
    if errs:
        abort(500, description=errs.decode('utf-8'))
    
    last_farm_summary = chia.FarmSummary(outs.decode('utf-8').splitlines())
    last_farm_summary_load_time = datetime.datetime.now()
    return last_farm_summary

def is_setup():
    # If farming, then need 'keys' variable set to a mnemonic.txt file or similar
    # See https://github.com/Chia-Network/chia-docker/blob/main/entrypoint.sh#L7
    return "keys" in os.environ and path.exists(os.environ['keys'])
