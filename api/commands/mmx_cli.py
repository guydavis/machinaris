#
# CLI interactions with the mmx binary.
#

import asyncio
import datetime
import json
import os
import pexpect
import psutil
import re
import signal
import shutil
import socket
import time
import traceback

from flask import Flask, jsonify, abort, request, flash
from stat import S_ISREG, ST_CTIME, ST_MTIME, ST_MODE, ST_SIZE
from subprocess import Popen, TimeoutExpired, PIPE, STDOUT
from os import path

from common.config import globals
from api import app
from api.models import mmx

def load_farm_info(blockchain):
    mmx_binary = globals.get_blockchain_binary(blockchain)
    if globals.farming_enabled():
        proc = Popen("{0} farm info && {0} wallet show && {0} node info".format(mmx_binary), stdout=PIPE, stderr=PIPE, shell=True)
        try:
            outs, errs = proc.communicate(timeout=90)
        except TimeoutExpired:
            proc.kill()
            proc.communicate()
            abort(500, description="The timeout is expired!")
        if errs:
            app.logger.debug("Error from {0} farm summary because {1}".format(blockchain, outs.decode('utf-8')))
        return mmx.FarmSummary(outs.decode('utf-8').splitlines(), blockchain)
    elif globals.harvesting_enabled():
        return mmx.HarvesterSummary()
    else:
        raise Exception("Unable to load farm summary on non-farmer and non-harvester.")

def list_plots():
    all_entries = []
    for dir_path in os.environ['plots_dir'].split(':'):
        try:
            entries = (os.path.join(dir_path, file_name) for file_name in os.listdir(dir_path))
            entries = ((os.stat(path), path) for path in entries)
            entries = ((stat[ST_MTIME], stat[ST_SIZE], path) for stat, path in entries if S_ISREG(stat[ST_MODE]))
            all_entries.extend(entries)
        except:
            app.logger.info("Failed to list files at {0}".format(dir_path))
            app.logger.info(traceback.format_exc())
    all_entries = sorted(all_entries, key=lambda entry: entry[0], reverse=True)
    plots_farming = mmx.FarmPlots(all_entries)
    return plots_farming

def load_config(blockchain):
    mainnet = globals.get_blockchain_network_path(blockchain)
    return open(f'{mainnet}/config/Node.json','r').read()

def save_config(config, blockchain):
    try:
        mainnet = globals.get_blockchain_network_path(blockchain)
        # Validate the json first
        json.load(config)
        # Save a copy of the old config file
        src=f'{mainnet}/config/Node.json'
        dst=f'{mainnet}/config/Node.json' + time.strftime("%Y%m%d-%H%M%S")+".yaml"
        shutil.copy(src,dst)
        # Now save the new contents to main config file
        with open(src, 'w') as writer:
            writer.write(config)
    except Exception as ex:
        app.logger.info(traceback.format_exc())
        raise Exception('Updated Node.json failed validation!\n' + str(ex))
    else:
        pass

def load_wallet_show(blockchain):
    mmx_binary = globals.get_blockchain_binary(blockchain)
    proc = Popen("({0} node info | grep Synced) && {0} wallet show".format(mmx_binary), stdout=PIPE, stderr=PIPE, shell=True)
    try:
        outs, errs = proc.communicate(timeout=90)
    except TimeoutExpired:
        proc.kill()
        proc.communicate()
        abort(500, description="The timeout is expired!")
    if errs:
        abort(500, description=errs.decode('utf-8'))
    return mmx.Wallet(outs.decode('utf-8'))

def load_blockchain_show(blockchain):
    mmx_binary = globals.get_blockchain_binary(blockchain)
    proc = Popen("{0} node info".format(mmx_binary), stdout=PIPE, stderr=PIPE, shell=True)
    try:
        outs, errs = proc.communicate(timeout=90)
    except TimeoutExpired:
        proc.kill()
        proc.communicate()
        abort(500, description="The timeout is expired!")
    if errs:
        abort(500, description=errs.decode('utf-8'))
    return mmx.Blockchain(outs.decode('utf-8').splitlines())

def load_connections_show(blockchain):
    mmx_binary = globals.get_blockchain_binary(blockchain)
    proc = Popen("{0} node peers".format(mmx_binary), stdout=PIPE, stderr=PIPE, shell=True)
    try:
        outs, errs = proc.communicate(timeout=90)
    except TimeoutExpired:
        proc.kill()
        proc.communicate()
        abort(500, description="The timeout is expired!")
    if errs:
        abort(500, description=errs.decode('utf-8'))
    return mmx.Connections(outs.decode('utf-8').splitlines())

def load_keys_show(blockchain):
    mmx_binary = globals.get_blockchain_binary(blockchain)
    proc = Popen("{0} wallet keys".format(mmx_binary), stdout=PIPE, stderr=PIPE, shell=True)
    try:
        outs, errs = proc.communicate(timeout=90)
    except TimeoutExpired:
        proc.kill()
        proc.communicate()
        abort(500, description="The timeout is expired!")
    if errs:
        abort(500, description=errs.decode('utf-8'))
    return mmx.Keys(outs.decode('utf-8').splitlines())
