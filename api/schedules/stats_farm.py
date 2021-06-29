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
        chia_farm_summary = chia_cli.load_farm_summary('chia')
        flax_farm_summary = None
        if globals.flax_enabled():
            flax_farm_summary = chia_cli.load_farm_summary('flax')
        db = get_db()
        cur = db.cursor()
        try:
            cur.execute("INSERT INTO stat_plot_count (value, created_at) VALUES (?,?)",
                        (chia_farm_summary.plot_count,current_datetime,))
        except:
            app.logger.info(traceback.format_exc())
        try:
            cur.execute("INSERT INTO stat_plots_size (value, created_at) VALUES (?,?)",
                        (converters.str_to_gibs(chia_farm_summary.plots_size),current_datetime,))
        except:
            app.logger.info(traceback.format_exc())
        if chia_farm_summary.status == "Farming":  # Only collect if fully synced
            try:
                cur.execute("INSERT INTO stat_total_chia (blockchain, value, created_at) VALUES ('chia',?,?)",
                            (chia_farm_summary.total_chia,current_datetime,))
            except:
                app.logger.info(traceback.format_exc())
            try:
                cur.execute("INSERT INTO stat_netspace_size (blockchain, value, created_at) VALUES ('chia',?,?)",
                            (converters.str_to_gibs(chia_farm_summary.netspace_size),current_datetime,))
            except:
                app.logger.info(traceback.format_exc())
            try:
                cur.execute("INSERT INTO stat_time_to_win (blockchain, value, created_at) VALUES ('chia',?,?)",
                            (converters.etw_to_minutes(chia_farm_summary.time_to_win),current_datetime,))
            except:
                app.logger.info(traceback.format_exc())
        if flax_farm_summary and flax_farm_summary.status == "Farming":  # Only collect if fully synced
            try:
                cur.execute("INSERT INTO stat_total_chia (blockchain, value, created_at) VALUES ('flax',?,?)",
                            (flax_farm_summary.total_chia,current_datetime,))
            except:
                app.logger.info(traceback.format_exc())
            try:
                cur.execute("INSERT INTO stat_netspace_size (blockchain, value, created_at) VALUES ('flax',?,?)",
                            (converters.str_to_gibs(flax_farm_summary.netspace_size),current_datetime,))
            except:
                app.logger.info(traceback.format_exc())
            try:
                cur.execute("INSERT INTO stat_time_to_win (blockchain, value, created_at) VALUES ('flax',?,?)",
                            (converters.etw_to_minutes(flax_farm_summary.time_to_win),current_datetime,))
            except:
                app.logger.info(traceback.format_exc())
        db.commit()
