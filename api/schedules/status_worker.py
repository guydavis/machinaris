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
from api.commands import chia_cli, chiadog_cli, plotman_cli, farmr_cli, mmx_cli
from api import app
from api import utils

def update():
    app.logger.info("Executing status_worker...")
    with app.app_context():
        try:
            hostname = utils.get_hostname()
            displayname = utils.get_displayname()
            config = globals.load()
            if config['farming_enabled'] or config['harvesting_enabled']:
                config['farmr_device_id'] = farmr_cli.load_device_id()
            payload = {
                "hostname": hostname,
                "blockchain": os.environ['blockchains'],
                "port": app.config['WORKER_PORT'],
                "displayname": displayname,
                "mode": os.environ['mode'],
                "services": gather_services_status(),
                "url": utils.get_worker_url(),
                "config": json.dumps(config),
            }
            utils.send_post('/workers/{0}/{1}'.format(hostname, app.config['WORKER_PORT']), payload, debug=False)
        except Exception as ex:
            app.logger.info("Failed to load and send worker status because {0}".format(str(ex)))

def gather_services_status():
    gc = globals.load()
    plotting_status = "disabled"
    if gc['plotting_enabled']:
        if plotman_cli.get_plotman_pid():
            plotting_status = "running"
        else:
            plotting_status = "stopped"
    archiving_status = "disabled"
    if gc['archiving_enabled']:
        if plotman_cli.get_archiver_pid():
            archiving_status = "running"
        else:
            archiving_status = "stopped"
    response = {
        'plotting_status': plotting_status,
        'archiving_status': archiving_status,
    }
    farming_status = "disabled"
    monitoring_status = "disabled"
    wallet_status = "disabled"
    # Assumes a single blockchain is enabled in this container
    blockchain = globals.enabled_blockchains()[0]
    if gc['farming_enabled'] or gc['harvesting_enabled']:
        if blockchain == 'mmx':
            farming_status = mmx_cli.load_farm_info(blockchain).status
        else:
            farming_status = chia_cli.load_farm_summary(blockchain).status
        if chiadog_cli.get_chiadog_pid(blockchain):
            monitoring_status = "running"
        else:
            monitoring_status = "stopped"
    response['monitoring_status'] = monitoring_status
    response['farming_status'] = farming_status
    if gc['machinaris_mode'] == 'fullnode':
        response['wallet_status'] = wallet_status
    return json.dumps(response)