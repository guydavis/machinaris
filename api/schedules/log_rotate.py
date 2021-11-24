#
# Performs an hourly log rotate of particularly egregious log files
# Useful for apps that do a poor job of this themselves
#

import os

LOG_ROTATE_CONFIG_DIR = '/etc/logrotate.d/'
LOG_ROTATE_CONFIGS = [
    'farmr'
]

def execute():
    for config in LOG_ROTATE_CONFIGS:
        if os.path.exists(LOG_ROTATE_CONFIG_DIR + config):
            os.system("usr/sbin/logroate -v " + LOG_ROTATE_CONFIG_DIR + config)
