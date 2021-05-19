#
# Common configuration functions.
#

import os

from app import app

def load():
    cfg = {}
    cfg['plotting_only'] = plotting_only()
    cfg['farming_only'] = farming_only()
    return cfg

def is_setup():
    if "keys" not in os.environ:
        app.logger.info("No 'keys' environment variable set for this run. Set an in-container path to mnemonic.txt.")
        return False
    keys = os.environ['keys'].split(':')
    foundKey = False
    for key in keys:
        if os.path.exists(key):
            foundKey = True
        else:
            app.logger.info("No such keys file: '{0}'".format(key))
            app.logger.info(os.listdir(key))
    return foundKey

def get_key_paths():
    if "keys" not in os.environ:
        app.logger.info("No 'keys' environment variable set for this run. Set an in-container path to mnemonic.txt.")
        return "<UNSET>"
    return os.environ['keys'].split(':')

def plotting_only():
    return "mode" in os.environ and os.environ['mode'] == "plotter"

def farming_only():
    return "mode" in os.environ and os.environ['mode'] in ["harvester", "farmer"]