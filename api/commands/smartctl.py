#
# Collect stats on drives using smartctl
#

import http
import json
import os
import requests

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
    #app.logger.info(cmd)
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

# If enhanced Chiadog is running within container, then its listening on http://localhost:8925
# Example: curl -X POST http://localhost:8925 -H 'Content-Type: application/json' -d '{"type":"user", "service":"farmer", "priority":"high", "message":"Hello World"}'
def notify_failing_device(ipaddr, device, status, debug=False):
    try:
        headers = {'Content-type': 'application/json', 'Accept': 'application/json'}
        if debug:
            http.client.HTTPConnection.debuglevel = 1
        mode = 'full_node'
        if 'mode' in os.environ and 'harvester' in os.environ['mode']:
            mode = 'harvester'
        response = requests.post("http://localhost:8925", headers = headers, data = json.dumps(
            {
                "type": "user", 
                "service": mode, 
                "priority": "high", 
                "message": "Device {0} on {1} reported a bad status: {2}".format(device, ipaddr, status)
            }
        ))
    except Exception as ex:
        app.logger.info("Failed to notify Chiadog of drive status change.")
    finally:
        http.client.HTTPConnection.debuglevel = 0
