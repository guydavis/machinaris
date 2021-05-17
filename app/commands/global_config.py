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
    # TODO One very first load, check that wallet has at least one key, else send here to create one
    # chia keys generate
    # chia keys show --show-mnemonic-seed | tail -n 1 > ${keys}
    return True

def plotting_only():
    return "plotter" in os.environ and os.environ['plotter'] == "true"

def farming_only():
    return ("harvester" in os.environ and os.environ['harvester'] == "true") \
        or ("farmer" in os.environ and os.environ['farmer'] == "true")