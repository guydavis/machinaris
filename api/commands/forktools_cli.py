#
# CLI interactions with the fork
#

import asyncio
import datetime
import os
import pexpect
import psutil
import re
import signal
import shutil
import socket
import time
import traceback
import yaml

from subprocess import Popen, TimeoutExpired, PIPE, STDOUT
from os import path

from api import app
from api.commands import chia_cli

def load_config(blockchain):
    return open('/root/.chia/forktools/ftconfigs/config.forkfixconfig','r').read()

def dispatch_action(job):
    service = job['service']
    if service != 'tools':
        raise Exception("Only forktools requests handled here!")
    action = job['action']
    if action == "update":
        settings = job['settings']
        for key in settings:
            app.logger.info("{0} -> {1}".format(key, settings[key]))
    else:
        raise Exception("Unsupported action {0} for monitoring.".format(action))

def exec_fixconfig():
    proc = Popen("echo 'Y' | ./forkfixconfig all", cwd='/forktools', stdout=PIPE, stderr=PIPE, shell=True)
    try:
        outs, errs = proc.communicate(timeout=90)
    except TimeoutExpired as ex:
        proc.kill()
        proc.communicate()
        app.logger.info(traceback.format_exc())
        return False
    if outs:
        app.logger.info("{0}".format(outs.decode('utf-8')))
    if errs:
        app.logger.info("{0}".format(errs.decode('utf-8')))
        return False
    return True

def save_config(config, blockchain):
    # Save a copy of the old config file
    src = "/root/.chia/forktools/ftconfigs/config.forkfixconfig"
    dst = "/root/.chia/forktools/ftconfigs/config.forkfixconfig." + \
        time.strftime("%Y%m%d-%H%M%S")
    shutil.copy(src, dst)
    # Now save the new contents to main config file
    with open(src, 'w') as writer:
        writer.write(config)
    app.logger.info("Executing forkfixconfig against updated configuration.")
    if exec_fixconfig():
        app.logger.info("Executing blockchain restart for {0}...".format(blockchain))
        chia_cli.restart_farmer(blockchain)
    else:
        app.logger.info("Failed to execute forkfixconfig using updated configuration.")
