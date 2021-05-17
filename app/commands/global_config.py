#
# Common configuration functions.
#

import os

def load():
    cfg = {}
    cfg['plotting_only'] = plotting_only()
    cfg['farming_only'] = farming_only()
    return cfg

def is_setup():
    return "keys" in os.environ and os.path.exists(os.environ['keys'])

def plotting_only():
    return "plotter" in os.environ and os.environ['plotter'] == "true"

def farming_only():
    return ("harvester" in os.environ and os.environ['harvester'] == "true") \
        or ("farmer" in os.environ and os.environ['farmer'] == "true")