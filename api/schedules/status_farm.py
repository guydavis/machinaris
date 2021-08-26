#
# Performs a REST call to controller (possibly localhost) of latest farm status.
#

import os
import traceback

from flask import g

from common.config import globals
from common.utils import converters
from api import app
from api.commands import chia_cli
from api import utils

# On initialization Chia outputs 
def safely_gather_plots_size_gibs(plots_size):
    plots_size_gibs = 0
    try:
        plots_size_gibs = converters.str_to_gibs(plots_size)
    except:
        app.logger.info("Unconvertable plots size: {0}  Using zero.".format(plots_size))
        plots_size_gibs = 0
    try:
        float(plots_size_gibs)
    except: 
        app.logger.info("Unfloatable plots size: {0}  Using zero.".format(plots_size))
        plots_size_gibs = 0
    return plots_size_gibs

def update():
    if not globals.farming_enabled() and not globals.harvesting_enabled():
        #app.logger.info("Skipping farm summary status collection on plotting-only instance.")
        return
    with app.app_context():
        try:
            hostname = utils.get_hostname()
            farm_summary = chia_cli.load_farm_summary('chia')
            payload = {
                "hostname": hostname,
                "mode": os.environ['mode'],
                "status": "" if not hasattr(farm_summary, 'status') else farm_summary.status,
                "plot_count": farm_summary.plot_count,
                "plots_size": safely_gather_plots_size_gibs(farm_summary.plots_size),
                "total_chia": 0 if not hasattr(farm_summary, 'total_chia') else farm_summary.total_chia,
                "netspace_size": 0 if not hasattr(farm_summary, 'netspace_size') else converters.str_to_gibs(farm_summary.netspace_size),
                "expected_time_to_win": "" if not hasattr(farm_summary, 'time_to_win') else farm_summary.time_to_win,
            }
            if globals.flax_enabled():
                flax_farm_summary = chia_cli.load_farm_summary('flax')
                payload.update({
                    "total_flax": 0 if not hasattr(flax_farm_summary, 'total_chia') else flax_farm_summary.total_chia,
                    "flax_netspace_size": 0 if not hasattr(flax_farm_summary, 'netspace_size') else converters.str_to_gibs(flax_farm_summary.netspace_size),
                    "flax_expected_time_to_win": "" if not hasattr(flax_farm_summary, 'time_to_win') else flax_farm_summary.time_to_win,
                })  
            utils.send_post('/farms/', payload, debug=True)
        except:
            app.logger.info("Failed to load farm summary and send.")
            app.logger.info(traceback.format_exc())
