#
#  Control of the Forktools configuration and services
#

from flask import Flask, jsonify, abort, request, flash, g

from common.models import alerts as a
from web import app, db, utils
from . import worker as wk

def load_config(farmer, blockchain):
    return utils.send_get(farmer, "/configs/tools/"+ blockchain, debug=False).content

def save_config(farmer, blockchain, config):
    try:
        utils.send_put(farmer, "/configs/tools/" + blockchain, config, debug=False)
    except Exception as ex:
        flash('Failed to save config to farmer.  Please check log files.', 'danger')
        flash(str(ex), 'warning')
    else:
        flash('Nice! Tools config validated and saved successfully. Worker services now restarting. Please allow 10-15 minutes to take effect.', 'success')
