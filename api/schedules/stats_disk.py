#
# Performs a regular insert of latest stats for disk usage
#

import datetime
import os
import shutil
import sqlite3
import socket
import traceback

from common.config import globals
from common.models import stats
from api import app, utils, db

DELETE_OLD_STATS_AFTER_DAYS = 1

TABLES = [ stats.StatPlotsTotalUsed, stats.StatPlotsDiskUsed, stats.StatPlotsDiskFree,
           stats.StatPlottingTotalUsed, stats.StatPlottingDiskUsed, stats.StatPlottingDiskFree, ]

def delete_old_stats():
    try:
        cutoff = datetime.datetime.now() - datetime.timedelta(days=DELETE_OLD_STATS_AFTER_DAYS)
        for table in TABLES:
            db.session.query(table).filter(table.created_at <= cutoff.strftime("%Y%m%d%H%M")).delete()
        db.session.commit()
    except:
        app.logger.info("Failed to delete old statistics.")
        app.logger.info(traceback.format_exc())

def store_disk_stats(current_datetime, disk_type):
    hostname = socket.gethostname()
    total_used = 0.0
    disks = globals.get_disks(disk_type)
    for disk in disks:
        if not os.path.exists(disk):
            app.logger.info("Skipping disk stat collection for non-existant path: {0}".format(disk))
            continue
        try:
            total, used, free = shutil.disk_usage(disk)
            if disk_type == 'plots':
                stat = stats.StatPlotsDiskUsed(hostname=hostname, path=disk, value=(used // (2**30)), created_at=current_datetime)
                db.session.add(stat)
                stat = stats.StatPlotsDiskFree(hostname=hostname, path=disk, value=(free // (2**30)), created_at=current_datetime)
                db.session.add(stat)
            elif disk_type == 'plotting':
                stat = stats.StatPlottingDiskUsed(hostname=hostname, path=disk, value=(used // (2**30)), created_at=current_datetime)
                db.session.add(stat)
                stat = stats.StatPlottingDiskFree(hostname=hostname, path=disk, value=(free // (2**30)), created_at=current_datetime)
                db.session.add(stat)
            db.session.commit()
            total_used += (free // (2**30))
        except:
            app.logger.info(
                "Failed to get usage of {0} disk: {1}".format(disk_type, disk))
            app.logger.info(traceback.format_exc())
    try:
        if disk_type == 'plots':
            stat = stats.StatPlotsTotalUsed(hostname=hostname, blockchain='chia', value=total_used, created_at=current_datetime)
            db.session.add(stat)
        elif disk_type == 'plotting':
            stat = stats.StatPlottingTotalUsed(hostname=hostname, blockchain='chia', value=total_used, created_at=current_datetime)
            db.session.add(stat)
        db.session.commit()
    except:
        app.logger.info(
            "Failed to store total used for {0} disks.".format(disk_type))
        app.logger.info(traceback.format_exc())

def collect():
    with app.app_context():
        app.logger.debug("Collecting stats about disks.")
        gc = globals.load()
        delete_old_stats()
        current_datetime = datetime.datetime.now().strftime("%Y%m%d%H%M")
        if gc['farming_enabled'] or gc['harvesting_enabled']:
            store_disk_stats(current_datetime, 'plots')
            if not gc['is_controller']: 
                send_stats(stats.StatPlotsDiskUsed, '/stats/plotsdiskused/')
                send_stats(stats.StatPlotsDiskFree, '/stats/plotsdiskfree/')
        if gc['plotting_enabled']:
            store_disk_stats(current_datetime, 'plotting')
            if not gc['is_controller']: 
                send_stats(stats.StatPlottingDiskUsed, '/stats/plottingdiskused/')
                send_stats(stats.StatPlottingDiskFree, '/stats/plottingdiskfree/')

def send_stats(model, endpoint):
    since = (datetime.datetime.now() - datetime.timedelta(minutes=15)).strftime("%Y-%m-%d %H:%M:%S.000")
    try:
        payload = []
        for stat in db.session.query(model).filter(model.created_at >= since).all():
            payload.append({
                "hostname": stat.hostname,
                "path": stat.path,
                "value": stat.value,
                "created_at": stat.created_at,
            })
        utils.send_post(endpoint, payload, debug=False)
    except:
        app.logger.info("Failed to load recent {0} stats and send.".format(endpoint))
        app.logger.info(traceback.format_exc())
