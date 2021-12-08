#
# CLI interactions with the blockchain binaries which support "official" pools
#

import datetime
import json
import os
import pexpect
import psutil
import re
import requests
import signal
import shutil
import socket
import sys
import time
import traceback
import urllib
import yaml

from flask import Flask, jsonify, abort, request, flash, url_for
from flask.helpers import make_response
from stat import S_ISREG, ST_CTIME, ST_MTIME, ST_MODE, ST_SIZE
from subprocess import Popen, TimeoutExpired, PIPE
from sqlalchemy import or_
from os import path

from web import app, db, utils
from common.models import plotnfts as pn, pools as po
from common.config import globals
from web.models.pools import Plotnfts, Pools
from . import worker as wk

def load_plotnfts():
    plotnfts = db.session.query(pn.Plotnft).all()
    return Plotnfts(plotnfts)

def load_pools():
    plotnfts = db.session.query(pn.Plotnft).all()
    pools = db.session.query(po.Pool).all()
    return Pools(pools, plotnfts)

def get_plotnft_log():
    try:
        return open('/root/.chia/mainnet/log/plotnft.log',"r").read()
    except:
        return None

def get_first_pool_wallet_id():
    for plotnft in load_plotnfts().rows:
        for line in plotnft['details'].splitlines():
            app.logger.info(line)
            m = re.search("Wallet id (\d+):", line)
            if m:
                return m.group(1)
    return None

def process_pool_save(choice, pool_url, current_pool_url):
    pool_wallet_id = get_first_pool_wallet_id()
    if choice == "self":
        if current_pool_url and pool_wallet_id:
            return process_pool_leave(choice, pool_wallet_id)
        elif not pool_wallet_id:
            return process_self_pool()
        else:
            flash('Already self-pooling your own NFT.  No changes made.', 'message')
            return False
    elif choice == "join":
        if current_pool_url == pool_url:
            flash('Already pooling with {0}.  No changes made.'.format(pool_url), 'message')
            return False
        return process_pool_join(choice, pool_url, pool_wallet_id)

def process_pool_leave(choice, wallet_index):
    chia_binary = globals.get_blockchain_binary('chia')
    cmd = "{0} plotnft leave -y -i {1}".format(chia_binary, wallet_index)
    app.logger.info("Attempting to leave pool: {0}".format(cmd))
    result = ""
    try:
        child = pexpect.spawn(cmd)
        child.logfile = sys.stdout.buffer
        while True:
            i = child.expect(["Choose wallet key:.*\r\n", pexpect.EOF])
            if i == 0:
                app.logger.info("plotnft got index prompt so selecting #{0}".format(wallet_index))
                child.sendline("{0}".format(wallet_index))
            elif i==1:
                app.logger.info("plotnft end of output...")
                result += child.before.decode("utf-8") + child.read().decode("utf-8")
                break
        if result:  # Chia outputs their errors to stdout, not stderr, so must check.
            stdout_lines = result.splitlines()
        out_file = '/root/.chia/mainnet/log/plotnft.log'
        with open(out_file, 'a') as f:
            f.write("\nchia plotnft plotnft leave -y -i 1 --> Executed at: {0}\n".format(time.strftime("%Y%m%d-%H%M%S")))
            for line in stdout_lines:
                f.write(line)
            f.write("\n**********************************************************************\n")
        for line in stdout_lines:
            if "Error" in line:
                flash('Error while leaving Chia pool.', 'danger')
                flash(line, 'warning')
                return False
    except Exception as ex:
        app.logger.info(traceback.format_exc())
        print(str(child))
        flash(str(ex), 'danger')
        return False
    time.sleep(15)
    try: # Trigger a status update
        requests.get("http://localhost:8927/plotnfts/", timeout=5)
    except:
        app.logger.info(traceback.format_exc())
    time.sleep(5)
    flash('Successfully left pool, switching to self plotting.  Please wait a while to complete, then refresh page. See below for details.', 'success')
    return True

def process_pool_join(choice, pool_url, pool_wallet_id):
    chia_binary = globals.get_blockchain_binary('chia')
    app.logger.info("Attempting to join pool at URL: {0} with wallet_id: {1}".format(pool_url, pool_wallet_id))
    try:
        if not pool_url.strip():
            raise Exception("Empty pool URL provided.")
        if not pool_url.startswith('https://') and not pool_url.startswith('http://'):
            pool_url = "https://" + pool_url
        result = urllib.parse.urlparse(pool_url)
        if result.scheme != 'https':
            raise Exception("Non-HTTPS scheme provided.")
        if not result.netloc:
            raise Exception("No hostname or IP provided.")
    except Exception as ex:
        app.logger.info(traceback.format_exc())
        flash('{0}'.format(str(ex)), 'danger')
        return False
    if pool_wallet_id: # Just joining a pool with existing NFT
        cmd = "{0} plotnft join -y -u {1} -i {2}".format(chia_binary, pool_url, pool_wallet_id)
        wallet_index = pool_wallet_id
    else:  # Both creating NFT and joining pool in one setp
        cmd = "{0} plotnft create -y -u {1} -s pool".format(chia_binary, pool_url)
        wallet_index = 1
    app.logger.info("Executing: {0}".format(cmd))
    result = ""
    try:
        child = pexpect.spawn(cmd)
        child.logfile = sys.stdout.buffer
        while True:
            i = child.expect(["Choose wallet key:.*\r\n", pexpect.EOF])
            if i == 0:
                app.logger.info("plotnft got index prompt so selecting #{0}".format(wallet_index))
                child.sendline("{0}".format(wallet_index))
            elif i==1:
                app.logger.info("plotnft end of output...")
                result += child.before.decode("utf-8") + child.read().decode("utf-8")
                break
        if result:  # Chia outputs their errors to stdout, not stderr, so must check.
            stdout_lines = result.splitlines()
            out_file = '/root/.chia/mainnet/log/plotnft.log'
            with open(out_file, 'a') as f:
                f.write("\n{0} --> Executed at: {1}\n".format(cmd, time.strftime("%Y%m%d-%H%M%S")))
                for line in stdout_lines:
                    f.write(line)
                f.write("\n**********************************************************************\n")
            for line in stdout_lines:
                if "Error" in line:
                    flash('Error while joining Chia pool. Please double-check pool URL: {0}'.format(pool_url), 'danger')
                    flash(line, 'warning')
                    return False
    except Exception as ex:
        app.logger.info(traceback.format_exc())
        print(str(child))
        flash(str(ex), 'danger')
        return False
    time.sleep(15)
    try: # Trigger a status update
        requests.get("http://localhost:8927/plotnfts/", timeout=5)
    except:
        app.logger.info(traceback.format_exc())
    time.sleep(5)
    flash('Successfully joined {0} pool by creating Chia NFT.  Please wait a while to complete, then refresh page. See below for details.'.format(pool_url), 'success')
    return True

def process_self_pool(wallet_index=1):
    chia_binary = globals.get_blockchain_binary('chia')
    cmd = "{0} plotnft create -y -s local".format(chia_binary)
    app.logger.info("Attempting to create NFT for self-pooling. {0}".format(cmd))
    result = ""
    try:
        child = pexpect.spawn(cmd)
        child.logfile = sys.stdout.buffer
        while True:
            i = child.expect(["Choose wallet key:.*\r\n", pexpect.EOF])
            if i == 0:
                app.logger.info("plotnft got index prompt so selecting #{0}".format(wallet_index))
                child.sendline("{0}".format(wallet_index))
            elif i==1:
                app.logger.info("plotnft end of output...")
                result += child.before.decode("utf-8") + child.read().decode("utf-8")
                break
        if result:  # Chia outputs their errors to stdout, not stderr, so must check.
            stdout_lines = result.splitlines()
        out_file = '/root/.chia/mainnet/log/plotnft.log'
        with open(out_file, 'a') as f:
            f.write("\n{0} --> Executed at: {1}\n".format(cmd, time.strftime("%Y%m%d-%H%M%S")))
            for line in stdout_lines:
                f.write(line)
            f.write("\n**********************************************************************\n")
        for line in stdout_lines:
            if "Error" in line:
                flash('Error while creating self-pooling NFT', 'danger')
                flash(line, 'warning')
                return False
    except Exception as ex:
        app.logger.info(traceback.format_exc())
        print(str(child))
        flash(str(ex), 'danger')
        return False
    time.sleep(15)
    try: # Trigger a status update
        requests.get("http://localhost:8927/plotnfts/", timeout=5)
    except:
        app.logger.info(traceback.format_exc())
    time.sleep(5)
    flash('Successfully created a NFT for self-pooling.  Please wait a while to complete, then refresh page. See below for details.', 'success')
    return True

def check_for_pool_requirements():
    pass