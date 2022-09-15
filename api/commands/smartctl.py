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
            if errs:
                app.logger.info("Error from smartctl scan because {0}".format(outs.decode('utf-8')))
        except TimeoutExpired:
            proc.kill()
            proc.communicate()
            raise Exception("The timeout for smartctl scan expired!")
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
        if errs:
            app.logger.error("Error from {0} because {1}".format(cmd, outs.decode('utf-8')))
            return None
    except TimeoutExpired:
        proc.kill()
        proc.communicate()
        app.logger.info("Error from {0} because timeout expired".format(cmd))
        return None
    # Handle Smartctl response code bits.  See 'Return Values' at https://linux.die.net/man/8/smartctl
    if (proc.returncode & (1<<0)):
        app.logger.info("Failed commandline parse of {0}".format(cmd))
        return None
    if (proc.returncode & (1<<1)):
        app.logger.info("Device open failed, device did not return an IDENTIFY DEVICE structure, or device is in a low-power mode. {0}".format(cmd))
        return None
    if (proc.returncode & (1<<2)):
        app.logger.info("Some SMART or other ATA command to the disk failed, or there was a checksum error in a SMART data structure. {0}".format(cmd))
        return None
    if (proc.returncode & (1<<3)):
        app.logger.info("SMART status check returned DISK FAILING")
    if (proc.returncode & (1<<4)):
        app.logger.info("Smartctl found prefail Attributes <= threshold.")
    if (proc.returncode & (1<<5)):
        app.logger.debug("SMART status check returned DISK OK but we found that some (usage or prefail) Attributes have been <= threshold at some time in the past.")
    if (proc.returncode & (1<<6)):
        app.logger.debug("The device error log contains records of errors.")
    if (proc.returncode & (1<<7)):
        app.logger.debug("The device self-test log contains records of errors. [ATA only] Failed self-tests outdated by a newer successful extended self-test are ignored.")
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
