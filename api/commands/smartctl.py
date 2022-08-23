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
    if len(data.keys()) > 0:
        app.logger.info("{0} contains: ".format(SMARTCTL_OVERRIDES_CONFIG))
        app.logger.info(data)
    for drive in data.keys():
        if 'device_type' in data[drive]:
            data[drive]['type_overridden'] = True
        if not 'comment' in data[drive]:
            data[drive]['comment'] = None
    return data

def load_drives_status():
    with app.app_context():
        proc = Popen("smartctl --scan", stdout=PIPE, stderr=PIPE, shell=True)
        try:
            outs, errs = proc.communicate(timeout=30)
        except TimeoutExpired:
            proc.kill()
            proc.communicate()
            raise Exception("The timeout for smartctl scan expired!")
        if errs:
            app.logger.info("Error from smartctl scan because {0}".format(outs.decode('utf-8')))
        devices = load_smartctl_overrides()
        # Now add devices from the scan only if 
        for line in outs.decode('utf-8').splitlines():
            # First parse the single device line from smartctl --scan
            # Example "/dev/sda -d sat # /dev/sda [SAT], ATA device"
            values = line.split('#')
            comment = values[1].strip()
            values = values[0].split('-d')
            device = values[0].strip()
            device_type = values[1].strip()
            if not device in devices:  # Add any devices from the scan, not in overrides
                devices[device] = {}
            if not 'device_type' in  devices[device]: # User added override device to list, but accepts default type
                devices[device]['device_type'] = device_type
            devices[device]['comment'] = comment
        drive_results = []
        for device in devices.keys():
            info = load_drive_info(device, devices[device])
            if info and not "No such device" in info:
                #app.logger.info("Smartctl info parsed and device added: {0}".format(device))
                drive_results.append(drives.DriveStatus(device, devices[device]['device_type'],
                    devices[device]['comment'], info))
            else:
                app.logger.info("Smartctl reports no useful info for {0}".format(device))
        return drive_results

def load_drive_info(device_name, device_settings):
    #app.logger.info("{0} -> {1}".format(device_name, device_settings))
    if 'type_overridden' in device_settings:
        cmd = "smartctl -a -n standby -d {0} {1}".format(device_settings['device_type'], device_name)
    else: # No override, use the default auto mode
        cmd = "smartctl -a -n standby {0}".format(device_name)
    app.logger.info("Executing: {0}".format(cmd))
    proc = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
    try:
        outs, errs = proc.communicate(timeout=10)
    except TimeoutExpired:
        proc.kill()
        proc.communicate()
        app.logger.info("Error from {0} because timeout expired".format(cmd))
        return None
    if proc.returncode != 0:
        app.logger.info("Non-zero exit code from {0} was {1}".format(cmd, proc.returncode))
        return None
    if errs:
        app.logger.info("Error from {0} because {1}".format(cmd, outs.decode('utf-8')))
        return None
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
