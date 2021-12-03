#
# Performs an hourly log rotate of particularly egregious log files
# Useful for apps that do a poor job of this themselves
#

import os

from api import app

MAX_LOG_SIZE_MB = 20
LOG_ROTATE_CONFIG_DIR = '/etc/logrotate.d/'
LOG_ROTATE_CONFIGS = [
    'farmr'
]

def execute():
    app.logger.info("Executing log rotation...")
    for config in LOG_ROTATE_CONFIGS:
        if os.path.exists(LOG_ROTATE_CONFIG_DIR + config):
            app.logger.info("Rotating config: " + LOG_ROTATE_CONFIG_DIR + config)
            os.system("/usr/sbin/logrotate " + LOG_ROTATE_CONFIG_DIR + config + " 2>&1 >/dev/null")

    # Extra guards for farmr which can eat GBs of log space sometimes
    for file in os.listdir("/root/.chia/farmr"):
        if file.startswith("log"):
            size_mbs = os.path.getsize(os.path.join("/root/.chia/farmr", file)) >> 20
            if (size_mbs > MAX_LOG_SIZE_MB): 
                app.logger.info("Deleting large farmr log at {0}".format(os.path.join("/root/.chia/farmr", file)))
                os.unlink(os.path.join("/root/.chia/farmr", file))