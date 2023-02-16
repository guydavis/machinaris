#
# Performs an hourly log rotate of particularly egregious log files
# Useful for apps that do a poor job of this themselves
#

import os
import subprocess

from api import app

MAX_LOG_SIZE_MB = 20
LOG_ROTATE_CONFIG_DIR = '/etc/logrotate.d/'
LOG_ROTATE_CONFIGS = [
    'machinaris',
    'mmx-node',
    'plotman',
]

def execute():
    for config in LOG_ROTATE_CONFIGS:
        if os.path.exists(LOG_ROTATE_CONFIG_DIR + config):
            app.logger.info("Rotating config: " + LOG_ROTATE_CONFIG_DIR + config)
            subprocess.call("/usr/sbin/logrotate " + LOG_ROTATE_CONFIG_DIR + config + " >/dev/null 2>&1", shell=True)
