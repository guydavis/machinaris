#
# Details for drives attached to workers
#

import datetime
import json
import os
import psutil
import re
import signal
import shutil
import socket
import time
import traceback
import yaml

from flask import Flask, jsonify, abort, request, flash
from flask_babel import _, lazy_gettext as _l

from common.models import drives as d
from web import app, db, utils
from web.models import drives

DRIVES_SETTINGS = '/root/.chia/machinaris/config/drives_settings.json'

def load_drive_summary():
    drvs = db.session.query(d.Drive).order_by(d.Drive.hostname, d.Drive.device).all()
    return drives.Drives(drvs)

def load_smartctl_info(hostname, device):
    drv = db.session.query(d.Drive).filter(d.Drive.hostname == hostname, d.Drive.device == device).first()
    if not drv or not drv.smart_info:
        return _('Oops! No smartctl info found for device %(device)s on %(hostname)s.', 
            device=device, hostname=hostname)
    return drv.smart_info

def save_settings(form):
    app.logger.info("good_below_temperature: {0}".format(form.get("good_below_temperature")))
    app.logger.info("warn_below_temperature: {0}".format(form.get("warn_below_temperature")))
    settings = {}
    try:
        with open(DRIVES_SETTINGS) as f:
            settings = json.load(f)
    except:
        pass
    try:
        settings['good_below_temperature'] = int(form.get("good_below_temperature"))
        settings['warn_below_temperature'] = int(form.get("warn_below_temperature"))
        with open(DRIVES_SETTINGS, 'w') as f:
            json.dump(settings, f)
    except Exception as ex:
        msg = "Unable to write drives settings to {0} because {1}".format(DRIVES_SETTINGS, str(ex))
        app.logger.error(msg)
        flash(_("Failed to save display settings. Please check Web Log."), 'danger')
        return {}
    flash(_("Saved display settings."), 'success')
    return settings

def load_settings():
    settings = {}
    try:
        with open(DRIVES_SETTINGS) as f:
            settings = json.load(f)
    except:
        settings['good_below_temperature'] = 40 # Default
        settings['warn_below_temperature'] = 50 # Default
    #app.logger.info("good_below_temperature: {0}".format(settings["good_below_temperature"]))
    #app.logger.info("warn_below_temperature: {0}".format(settings["warn_below_temperature"]))
    return settings