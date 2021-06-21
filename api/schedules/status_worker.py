#
# Performs a REST call to controller (possibly localhost) of latest farm status.
#


import datetime
import http
import json
import os
import requests
import socket
import sqlite3
import traceback

from flask import g

from common.config import globals
from api.commands import chia_cli, chiadog_cli, plotman_cli
from api import app
from api import utils

def update():
    with app.app_context():
        try:
            hostname = utils.get_hostname()
            payload = {
                "hostname": hostname,
                "mode": os.environ['mode'],
                "services": gather_services_status(),
                "url": utils.get_remote_url(),
                "config": json.dumps(globals.load()),
            }
            utils.send_post('/workers/', payload, debug=False)
        except:
            app.logger.info("Failed to load and send worker status.")
            app.logger.info(traceback.format_exc())

def gather_services_status():
    gc = globals.load()
    plotman_status = "disabled"
    if gc['plotting_enabled']:
        if plotman_cli.get_plotman_pid():
            plotman_status = "running"
        else:
            plotman_status = "stopped"
    archiver_status = "disabled"
    if gc['archiving_enabled']:
        if plotman_cli.get_archiver_pid():
            archiver_status = "running"
        else:
            archiver_status = "stopped"
    chia_farm_status = "disabled"
    chiadog_status = "disabled"
    if gc['farming_enabled']:
        chia_farm_status = chia_cli.load_farm_summary().status
    if gc['farming_enabled'] or gc['harvesting_enabled']:
        if chiadog_cli.get_chiadog_pid():
            chiadog_status = "running"
        else:
            chiadog_status = "stopped"
    return json.dumps({
        'plotman_status': plotman_status,
        'archiver_status': archiver_status,
        'chia_farm_status': chia_farm_status,
        'chiadog_status': chiadog_status
    })