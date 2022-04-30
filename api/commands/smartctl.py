#
# Collect stats on drives using smartctl
#

import json
import os

from flask import Flask, jsonify, abort, request, flash
from subprocess import Popen, TimeoutExpired, PIPE, STDOUT

from api import app
from api.models import drives

SMARTCTL_OVERRIDES_CONFIG = '/root/.chia/machinaris/config/drives_overrides.json'

def load_smartctl_overrides():
    data = {}
    if os.path.exists(SMARTCTL_OVERRIDES_CONFIG):
        try:
            with open(SMARTCTL_OVERRIDES_CONFIG) as f:
                data = json.load(f)
        except Exception as ex:
            msg = "Unable to read smartctl overrides from {0} because {1}".format(SMARTCTL_OVERRIDES_CONFIG, str(ex))
            app.logger.error(msg)
            return data
    return data

def load_drives_status():
    with app.app_context():
        proc = Popen("smartctl --scan", stdout=PIPE, stderr=PIPE, shell=True)
        try:
            outs, errs = proc.communicate(timeout=90)
        except TimeoutExpired:
            proc.kill()
            proc.communicate()
            abort(500, description="The timeout is expired!")
        if errs:
            app.logger.info("Error from smartctl scan because {0}".format(outs.decode('utf-8')))
        overrides = load_smartctl_overrides()
        devices = []
        for line in outs.decode('utf-8').splitlines():
            pieces = line.split()
            device = pieces[0]
            info = load_drive_info(device, overrides)
            devices.append(drives.DriveStatus(line, info))
        return devices

def load_drive_info(device, overrides):
    if device in overrides and 'device_type' in overrides[device]:
        cmd = "smartctl -a -d {0} {1}".format(overrides[device]['device_type'], device)
    else: # No override, use the default auto mode
        cmd = "smartctl -a {0}".format(device)
    app.logger.info(cmd)
    proc = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
    try:
        outs, errs = proc.communicate(timeout=90)
    except TimeoutExpired:
        proc.kill()
        proc.communicate()
        app.logger.info("Error from {0} because timeout expired".format(cmd))
        return None
    if errs:
        app.logger.debug("Error from {0} because {1}".format(cmd, outs.decode('utf-8')))
    return outs.decode('utf-8')
