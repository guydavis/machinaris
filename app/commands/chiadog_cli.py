#
# CLI interactions with the chiadog script.
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
from app.models import chiadog
from app import app

def save_config(config):
    try:
        # Validate the YAML first
        yaml.safe_load(config)
        # Save a copy of the old config file
        src="/root/.chia/chiadog/config.yaml"
        dst="/root/.chia/chiadog/config.yaml."+time.strftime("%Y%m%d-%H%M%S")+".yaml"
        shutil.copy(src,dst)
        # Now save the new contents to main config file
        with open(src, 'w') as writer:
            writer.write(config)
    except Exception as ex:
        traceback.print_exc()
        flash('Updated config.yaml failed validation! Fix and save or refresh page.', 'danger')
        flash(str(ex), 'warning')
    else:
        flash('Nice! Chiadog\'s config.yaml validated and saved successfully.', 'success')
        if get_chiadog_pid():
            flash('NOTE: Please restart Chiadog on the Alerts page to pickup your changes.', 'info')


def get_chiadog_pid():
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        if proc.info['name'] == 'python3' and '/root/.chia/chiadog/config.yaml' in proc.info['cmdline']:
            return proc.info['pid']
    return None
