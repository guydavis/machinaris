#
# Performs a regular insert of latest stats for disk usage
#

import datetime
import shutil
import sqlite3
import socket
import traceback

from flask import g

from common.config import globals
from api import app

DATABASE = '/root/.chia/machinaris/dbs/stats.db'

TABLES = ['stat_plots_total_used', 'stat_plots_disk_used', 'stat_plots_disk_free',
          'stat_plotting_total_used', 'stat_plotting_disk_used', 'stat_plotting_disk_free']

DELETE_OLD_STATS_AFTER_DAYS = 2

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
            cur.execute("DELETE FROM {0} WHERE created_at < {1}".format(
                table, cutoff.strftime("%Y%m%d%H%M")))
        db.commit()
    except:
        app.logger.info("Failed to delete old statistics.")
        app.logger.info(traceback.format_exc())


def store_disk_stats(db, current_datetime, disk_type):
    hostname = socket.gethostname()
    total_used = 0.0
    cur = db.cursor()
    disks = globals.get_disks(disk_type)
    for disk in disks:
        try:
            total, used, free = shutil.disk_usage(disk)
            cur.execute("INSERT INTO stat_{0}_disk_used (hostname, path, value, created_at) VALUES (?,?,?,?)".format(disk_type),
                        (hostname, disk, (used // (2**30)), current_datetime,))
            cur.execute("INSERT INTO stat_{0}_disk_free (hostname, path, value, created_at) VALUES (?,?,?,?)".format(disk_type),
                        (hostname, disk, (free // (2**30)), current_datetime,))
            db.commit()
            total_used += (free // (2**30))
        except:
            app.logger.info(
                "Failed to get usage of {0} disk: {1}".format(disk_type, disk))
            app.logger.info(traceback.format_exc())
    try:
        cur.execute("INSERT INTO stat_{0}_total_used (value, created_at) VALUES (?,?)".format(disk_type),
                    (total_used, current_datetime,))
        db.commit()
    except:
        app.logger.info(
            "Failed to store total used for {0} disks.".format(disk_type))
        app.logger.info(traceback.format_exc())


def collect():
    with app.app_context():
        app.logger.debug("Collecting stats about disks.")
        gc = globals.load()
        db = get_db()
        delete_old_stats(db)
        current_datetime = datetime.datetime.now().strftime("%Y%m%d%H%M")
        store_disk_stats(db, current_datetime, 'plots')
        if gc['plotting_enabled']:
            store_disk_stats(db, current_datetime, 'plotting')
