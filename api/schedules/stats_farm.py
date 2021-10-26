#
# Performs an hourly insert of latest stats for the farm summary
#

import datetime
import sqlite3
import traceback

from flask import g

from common.config import globals
from common.utils import converters
from api import app, utils
from api.commands import chia_cli

DELETE_OLD_STATS_AFTER_DAYS = 30

DATABASE = '/root/.chia/machinaris/dbs/stats.db'

TABLES = ['stat_plot_count', 'stat_plots_size', 'stat_total_chia',
          'stat_netspace_size', 'stat_time_to_win']

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

def delete_old_stats(db):
    try:
        cutoff = datetime.datetime.now() - datetime.timedelta(days=DELETE_OLD_STATS_AFTER_DAYS)
        cur = db.cursor()
        for table in TABLES:
            cur.execute("DELETE FROM {0} WHERE hostname IS NULL".format(table))
            cur.execute("DELETE FROM {0} WHERE created_at < {1}".format(
                table, cutoff.strftime("%Y%m%d%H%M")))
        db.commit()
    except:
        app.logger.info("Failed to delete old statistics.")
        app.logger.info(traceback.format_exc())

def collect():
    with app.app_context():
        gc = globals.load()
        db = get_db()
        delete_old_stats(db)
        if not gc['farming_enabled']:
            app.logger.debug(
                "Skipping farm summary stats collection as not farming on this Machinaris instance.")
            return
        app.logger.debug("Collecting stats about the farm.")
        current_datetime = datetime.datetime.now().strftime("%Y%m%d%H%M")
        for blockchain in globals.enabled_blockchains():
            farm_summary = chia_cli.load_farm_summary(blockchain)
            store_locally(db, farm_summary, current_datetime)
            if not gc['is_controller']:
                send_to_controller(blockchain, farm_summary, current_datetime)

def store_locally(db, farm_summary, current_datetime):
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
            cur.execute("INSERT INTO stat_total_chia (blockchain, value, created_at) VALUES ('chia',?,?)",
                        (farm_summary.total_coins,current_datetime,))
        except:
            app.logger.info(traceback.format_exc())
        try:
            cur.execute("INSERT INTO stat_netspace_size (blockchain, value, created_at) VALUES ('chia',?,?)",
                        (converters.str_to_gibs(farm_summary.netspace_size),current_datetime,))
        except:
            app.logger.info(traceback.format_exc())
        try:
            cur.execute("INSERT INTO stat_time_to_win (blockchain, value, created_at) VALUES ('chia',?,?)",
                        (converters.etw_to_minutes(farm_summary.time_to_win),current_datetime,))
        except:
            app.logger.info(traceback.format_exc())
    db.commit()

def send_to_controller(blockchain, farm_summary, current_datetime):
       send_stat(blockchain, '/stats/plotcount', farm_summary.plot_count,current_datetime)
       send_stat(blockchain, '/stats/plotssize', converters.str_to_gibs(farm_summary.plots_size),current_datetime)
       if farm_summary.status == "Farming":  # Only collect if fully synced
            send_stat(blockchain, '/stats/totalchia', farm_summary.total_coins, current_datetime)
            send_stat(blockchain, '/stats/netspacesize', converters.str_to_gibs(farm_summary.netspace_size) ,current_datetime)
            send_stat(blockchain, '/stats/timetowin', converters.etw_to_minutes(farm_summary.time_to_win), current_datetime)

def send_stat(blockchain, endpoint, value, current_datetime):
    try:
        payload = []
        payload.append({
            "hostname": utils.get_hostname(),
            "blockchain": blockchain,
            "value": value,
            "created_at": current_datetime,
        })
        utils.send_post(endpoint, payload, debug=False)
    except:
        app.logger.info("Failed to send latest stat to {0}.".format(endpoint))
        app.logger.info(traceback.format_exc())
