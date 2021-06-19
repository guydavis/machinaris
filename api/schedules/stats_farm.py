#
# Performs an hourly insert of latest stats for the farm summary
#

import datetime
import sqlite3
import traceback

from flask import g

from common.config import globals
from common.utils import converters
from api import app
from api.commands import chia_cli

DATABASE = '/root/.chia/machinaris/dbs/stats.db'


def get_db():
    db = getattr(g, '_stats_database', None)
    if db is None:
        db = g._stats_database = sqlite3.connect(DATABASE)
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_stats_database', None)
    if db is not None:
        db.close()


def collect():
    if not globals.farming_enabled():
        app.logger.debug(
            "Skipping farm summary stats collection as not farming on this Machinaris instance.")
        return
    with app.app_context():
        app.logger.debug("Collecting stats about farms.")
        current_datetime = datetime.datetime.now().strftime("%Y%m%d%H%M")
        farm_summary = chia_cli.load_farm_summary()
        db = get_db()
        cur = db.cursor()
        try:
            cur.execute("INSERT INTO stat_plot_count (value, created_at) VALUES (?,?)",
                        (farm_summary.plot_count,current_datetime,))
        except:
            app.logger.info(traceback.format_exc())
        try:
            cur.execute("INSERT INTO stat_plots_size (value, created_at) VALUES (?,?)",
                        (converters.str_to_gibs(farm_summary.plots_size),current_datetime,))
        except:
            app.logger.info(traceback.format_exc())
        if farm_summary.status == "Farming":  # Only collect if fully synced
            try:
                cur.execute("INSERT INTO stat_total_chia (value, created_at) VALUES (?,?)",
                            (farm_summary.total_chia,current_datetime,))
            except:
                app.logger.info(traceback.format_exc())
            try:
                cur.execute("INSERT INTO stat_netspace_size (value, created_at) VALUES (?,?)",
                            (converters.str_to_gibs(farm_summary.netspace_size),current_datetime,))
            except:
                app.logger.info(traceback.format_exc())
            try:
                cur.execute("INSERT INTO stat_time_to_win (value, created_at) VALUES (?,?)",
                            (converters.etw_to_minutes(farm_summary.time_to_win),current_datetime,))
            except:
                app.logger.info(traceback.format_exc())
        db.commit()
