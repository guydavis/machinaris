#
# Collect stats on drives using smartctl
#

from flask import Flask, jsonify, abort, request, flash
from subprocess import Popen, TimeoutExpired, PIPE, STDOUT

from api import app
from api.models import drives

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
        devices = []
        for line in outs.decode('utf-8').splitlines():
            pieces = line.split()
            device = pieces[0]
            info = load_drive_info(device)
            devices.append(drives.DriveStatus(line, info))
        return devices

def load_drive_info(device):
    cmd = "smartctl -a {0}".format(device)
    #app.logger.info(cmd)
    proc = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
    try:
        outs, errs = proc.communicate(timeout=90)
    except TimeoutExpired:
        proc.kill()
        proc.communicate()
        app.logger.info("Error from smartctl -a {0} because timeout expired".format(device))
        return None
    if errs:
        app.logger.debug("Error from smartctl all because {0}".format(outs.decode('utf-8')))
    return outs.decode('utf-8')
