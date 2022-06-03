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

from flask_babel import _, lazy_gettext as _l
from stat import S_ISREG, ST_CTIME, ST_MTIME, ST_MODE, ST_SIZE
from subprocess import Popen, TimeoutExpired, PIPE
from sqlalchemy import or_
from os import path

from api import app, utils
from common.models import plotnfts as pn, pools as po
from common.config import globals
from api.models.pools import Plotnfts

def get_job_parameter(job, key, index):
    if key in job:
        if index < len(job[key]):
            value = job[key][index].strip()
            if value and value != 'None':
                return value
        else:
            app.logger.info("No index {0} for key {1} found in: {2}".format(index, key, job[key]))
    else:
        app.logger.info("No key {0} found in job: {1}".format(key, job))
    return None

def dispatch_action(job):
    service = job['service']
    if service != 'pooling':
        raise Exception("Only pooling requests handled here!")
    action = job['action']
    if action == "save":
        app.logger.info("Processing pool save: {0}".format(job))
        # Loop thru the provided launcher_ids
        msg = ""
        blockchain = job["blockchain"]
        for i in range(len(job["launcher_ids"])):
            launcher_id = get_job_parameter(job,"launcher_ids", i)
            pool_wallet_id = get_job_parameter(job,"wallet_nums", i)
            choice = get_job_parameter(job,"choices", i)
            pool_url = get_job_parameter(job,"pool_urls", i)
            current_pool_url = get_job_parameter(job,"current_pool_urls", i)
            result = process_pool_save(blockchain, choice, pool_wallet_id, pool_url, current_pool_url, launcher_id)
            if result:
                msg += result + ' '
            else:
                app.logger.info("process_pool_save returned None for launcher_id index {0}".format(i))
        if msg.strip():
            return msg
        else:
            return _("No requested pool modifications were sent. Current settings are unchanged.")
    else:
        raise Exception("Unsupported action {0} for pools.".format(action))

def get_plotnft_log():
    try:
        return open('/root/.{0}/mainnet/log/plotnft.log'.format(os.environ['blockchains']),"r").read()
    except:
        return None

def get_pool_login_link(launcher_id):
    try:
        stream = os.popen("chia plotnft get_login_link -l {0}".format(launcher_id))
        return stream.read()
    except Exception as ex:
        app.logger.debug("Failed to get_login_link: {0}".format(str(ex)))
    return ""

def load_plotnft_show(blockchain):
    chia_binary = globals.get_blockchain_binary(blockchain)
    wallet_show = ""
    child = pexpect.spawn("{0} plotnft show".format(chia_binary))
    pool_wallet_id = 1
    while True:
        i = child.expect(["Wallet height:.*\r\n", "Wallet keys:.*\r\n", "No online backup file found.*\r\n"], timeout=120)
        if i == 0:
            app.logger.debug("wallet show returned 'Wallet height...' so collecting details.")
            wallet_show += child.after.decode("utf-8") + child.before.decode("utf-8") + child.read().decode("utf-8")
            break
        elif i == 1:
            app.logger.debug("wallet show got index prompt so selecting #{0}".format(pool_wallet_id))
            child.sendline("{0}".format(pool_wallet_id))
            pool_wallet_id += 1
        elif i == 2:
            child.sendline("S")
        else:
            app.logger.debug("pexpect returned {0}".format(i))
            wallet_show += "ERROR:\n" + child.after.decode("utf-8") + child.before.decode("utf-8") + child.read().decode("utf-8")
    return Plotnfts(wallet_show)

def process_pool_save(blockchain, choice, pool_wallet_id, pool_url, current_pool_url, launcher_id):
    if choice == "self":
        if current_pool_url and pool_wallet_id:
            return process_pool_leave(blockchain, pool_wallet_id)
        elif not pool_wallet_id:
            return process_self_pool(blockchain, pool_wallet_id)
        else:
            app.logger.info('Already self-pooling your own NFT.  No changes made to {0}'.format(launcher_id))
            return ""
    elif choice == "join":
        if current_pool_url == pool_url:
            app.logger.info('Already pooling with {0}.  No changes made to {1}'.format(pool_url, launcher_id))
            return ""
        return process_pool_join(blockchain, pool_url, pool_wallet_id)
    raise Exception("Unknown pool save choice provided: {0}".format(choice))

def process_pool_leave(blockchain, pool_wallet_id):
    chia_binary = globals.get_blockchain_binary(blockchain)
    cmd = "{0} plotnft leave -y -i {1}".format(chia_binary, pool_wallet_id)
    app.logger.info("Attempting to leave pool: {0}".format(cmd))
    result = ""
    child = pexpect.spawn(cmd)
    child.logfile = sys.stdout.buffer
    while True:
        i = child.expect(["Wallet keys:.*\r\n", pexpect.EOF])
        if i == 0:
            app.logger.info("plotnft got index prompt so selecting #{0}".format(pool_wallet_id))
            child.sendline("{0}".format(pool_wallet_id))
        elif i==1:
            app.logger.info("plotnft end of output...")
            result += child.before.decode("utf-8") + child.read().decode("utf-8")
            break
    if result:  # Chia outputs their errors to stdout, not stderr, so must check.
        stdout_lines = result.splitlines()
    out_file = '/root/.chia/machinaris/logs/plotnft.log'
    with open(out_file, 'a') as f:
        f.write("\n{0} plotnft plotnft leave -y -i 1 --> Executed at: {1}\n".format(blockchain, time.strftime("%Y%m%d-%H%M%S")))
        for line in stdout_lines:
            f.write(line)
        f.write("\n**********************************************************************\n")
    for line in stdout_lines:
        if "Error" in line:
            raise Exception('Error while leaving pool: ' + line)
    return _('Successfully left pool, switching to self-pooling. Please wait a few minutes or more to complete. DO NOT immediately re-submit your request. View the log for details.')

def process_pool_join(blockchain, pool_url, pool_wallet_id):
    chia_binary = globals.get_blockchain_binary(blockchain)
    app.logger.info("Attempting to join pool at URL: {0} with wallet_id: {1}".format(pool_url, pool_wallet_id))
    if not pool_url.strip():
        raise Exception("Empty pool URL provided.")
    if not pool_url.startswith('https://') and not pool_url.startswith('http://'):
        pool_url = "https://" + pool_url
    result = urllib.parse.urlparse(pool_url)
    if result.scheme != 'https':
        raise Exception("Non-HTTPS scheme provided.")
    if not result.netloc:
        raise Exception("No hostname or IP provided.")
    if pool_wallet_id: # Just joining a pool with existing NFT
        cmd = "{0} plotnft join -y -u {1} -i {2}".format(chia_binary, pool_url, pool_wallet_id)
        pool_wallet_id = pool_wallet_id
    else:  # Both creating NFT and joining pool in one setp
        cmd = "{0} plotnft create -y -u {1} -s pool".format(chia_binary, pool_url)
        pool_wallet_id = 1
    app.logger.info("Executing: {0}".format(cmd))
    result = ""
    child = pexpect.spawn(cmd)
    child.logfile = sys.stdout.buffer
    while True:
        i = child.expect(["Wallet keys:.*\r\n", pexpect.EOF])
        if i == 0:
            app.logger.info("plotnft got index prompt so selecting #{0}".format(pool_wallet_id))
            child.sendline("{0}".format(pool_wallet_id))
        elif i==1:
            app.logger.info("plotnft end of output...")
            result += child.before.decode("utf-8") + child.read().decode("utf-8")
            break
    if result:  # Chia outputs their errors to stdout, not stderr, so must check.
        stdout_lines = result.splitlines()
        out_file = '/root/.chia/machinaris/logs/plotnft.log'
        with open(out_file, 'a') as f:
            f.write("\n{0} --> Executed at: {1}\n".format(cmd, time.strftime("%Y%m%d-%H%M%S")))
            for line in stdout_lines:
                f.write(line)
            f.write("\n**********************************************************************\n")
        for line in stdout_lines:
            if "Error" in line:
                raise Exception('Error while joining Chia pool. Please double-check pool URL: {0} {1}'.format(pool_url, line))
    return _('Successfully joined %(pool_url)s pool by creating Chia NFT.  Please wait a few minutes or more to complete. DO NOT immediately re-submit your request. Be patient! View the log for details.', pool_url=pool_url)

def process_self_pool(blockchain, pool_wallet_id):
    chia_binary = globals.get_blockchain_binary(blockchain)
    cmd = "{0} plotnft create -y -s local".format(chia_binary)
    app.logger.info("Attempting to create NFT for self-pooling. {0}".format(cmd))
    result = ""
    child = pexpect.spawn(cmd)
    child.logfile = sys.stdout.buffer
    while True:
        i = child.expect(["Wallet keys:.*\r\n", pexpect.EOF])
        if i == 0:
            app.logger.info("plotnft got index prompt so selecting #{0}".format(pool_wallet_id))
            child.sendline("{0}".format(pool_wallet_id))
        elif i==1:
            app.logger.info("plotnft end of output...")
            result += child.before.decode("utf-8") + child.read().decode("utf-8")
            break
    if result:  # Chia outputs their errors to stdout, not stderr, so must check.
        stdout_lines = result.splitlines()
    out_file = '/root/.chia/machinaris/logs/plotnft.log'
    with open(out_file, 'a') as f:
        f.write("\n{0} --> Executed at: {1}\n".format(cmd, time.strftime("%Y%m%d-%H%M%S")))
        for line in stdout_lines:
            f.write(line)
        f.write("\n**********************************************************************\n")
    for line in stdout_lines:
        if "Error" in line:
            raise Exception('Error while creating self-pooling NFT: {0}'.format(line))
    return _('Successfully created a NFT for self-pooling.  Please wait a few minutes or more to complete. DO NOT immediately re-submit your request. Be patient! View the log for details.')
