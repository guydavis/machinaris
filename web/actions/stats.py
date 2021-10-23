#
# Access to statistics and calculated values.
#

import datetime
from shutil import disk_usage
import sqlite3

from flask import g
from sqlalchemy import or_

from common.utils import converters
from common.models.alerts import Alert
from common.models.stats import StatPlotCount, StatPlotsSize, StatTotalChia, StatNetspaceSize, StatTimeToWin, \
        StatPlotsTotalUsed, StatPlotsDiskUsed, StatPlotsDiskFree, StatPlottingTotalUsed, \
        StatPlottingDiskUsed, StatPlottingDiskFree
from web import app, db, utils
from web.actions import chia

DATABASE = '/root/.chia/machinaris/dbs/stats.db'

ALL_TABLES_BY_HOSTNAME = [
    'stat_plots_disk_used',
    'stat_plotting_disk_used',
    'stat_plots_disk_free',
    'stat_plotting_disk_free',
]

def get_stats_db():
    db = getattr(g, '_stats_database', None)
    if db is None:
        db = g._stats_database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_stats_database', None)
    if db is not None:
        db.close()

def load_daily_diff(farm_summary):
    for blockchain in farm_summary.farms:
        summary = {}
        # initialize defaults
        since_date = datetime.datetime.now() - datetime.timedelta(hours=24)
        since_str = since_date.strftime("%Y%m%d%H%M%S")
        summary['plot_count'] = plot_count_diff(since_str)
        summary['plots_size'] = plots_size_diff(since_str)
        summary['total_coin'] = total_coin_diff(since_str, blockchain)
        summary['netspace_size'] = netspace_size_diff(since_str, blockchain)
        #app.logger.info("{0} -> {1}".format(blockchain, summary))
        farm_summary.farms[blockchain]['daily_diff'] = summary

def plot_count_diff(since):
    result = ''
    try:
        latest = db.session.query(StatPlotCount).order_by(StatPlotCount.created_at.desc()).limit(1).first()
        #app.logger.debug(latest.value)
        before = db.session.query(StatPlotCount).filter(StatPlotCount.created_at <= since).order_by(StatPlotCount.created_at.desc()).limit(1).first()
        #app.logger.debug(before.value)
        if (latest.value - before.value) != 0:
            result = "%+0g in last day." % (latest.value - before.value)
    except Exception as ex:
        app.logger.debug("Failed to query for day diff of plot_count because {0}".format(str(ex)))
    #app.logger.debug("Result is: {0}".format(result))
    return result

def plots_size_diff(since):
    result = ''
    try:
        latest = db.session.query(StatPlotsSize).order_by(StatPlotsSize.created_at.desc()).limit(1).first()
        #app.logger.debug(latest.value)
        before = db.session.query(StatPlotsSize).filter(StatPlotsSize.created_at <= since).order_by(StatPlotsSize.created_at.desc()).limit(1).first()
        #app.logger.debug(before.value)
        gibs = (latest.value - before.value)
        fmtted = converters.gib_to_fmt(gibs)
        if fmtted == "0.000 B":
            result = ""
        elif not fmtted.startswith('-'):
            result = "+{0} in last day.".format(fmtted)
        else:
            result = fmtted
    except Exception as ex:
        app.logger.debug("Failed to query for day diff of plots_size because {0}".format(str(ex)))
    #app.logger.debug("Result is: {0}".format(result))
    return result

def total_coin_diff(since, blockchain):
    result = ''
    try:
        latest = db.session.query(StatTotalChia).filter(StatTotalChia.blockchain==blockchain).order_by(StatTotalChia.created_at.desc()).limit(1).first()
        #app.logger.debug(latest.value)
        before = db.session.query(StatTotalChia).filter(StatTotalChia.blockchain==blockchain, StatTotalChia.created_at <= since).order_by(StatTotalChia.created_at.desc()).limit(1).first()
        #app.logger.debug(before.value)
        if (latest.value - before.value) != 0:
            result = "%+6g in last day." % (latest.value - before.value)
    except Exception as ex:
        app.logger.debug("Failed to query for day diff of total_chia because {0}".format(str(ex)))
    #app.logger.debug("Result is: {0}".format(result))
    return result

def netspace_size_diff(since, blockchain):
    result = ''
    try:
        latest = db.session.query(StatNetspaceSize).filter(StatNetspaceSize.blockchain==blockchain).order_by(StatNetspaceSize.created_at.desc()).limit(1).first()
        #app.logger.debug(latest.value)
        before = db.session.query(StatNetspaceSize).filter(StatNetspaceSize.blockchain==blockchain, StatNetspaceSize.created_at <= since).order_by(StatNetspaceSize.created_at.desc()).limit(1).first()
        #app.logger.debug(before.value)
        gibs = (latest.value - before.value)
        fmtted = converters.gib_to_fmt(gibs)
        if fmtted == "0.000 B":
            result = ""
        elif not fmtted.startswith('-'):
            result = "+{0} in last day.".format(fmtted)
        else:
            result = "{0} in last day.".format(fmtted)
    except Exception as ex:
        app.logger.debug("Failed to query for day diff of netspace_size because {0}".format(str(ex)))
    #app.logger.debug("Result is: {0}".format(result))
    return result

def load_daily_farming_summaries():
    summary_by_workers = {}
    since_date = datetime.datetime.now() - datetime.timedelta(hours=24)
    for host in chia.load_farmers():
        summary_by_workers[host.displayname] = {}
        for wk in host.workers:
            summary_by_workers[host.displayname][wk['blockchain']] = daily_summaries(since_date, wk['hostname'], wk['displayname'], wk['blockchain']), 
    return summary_by_workers

def daily_summaries(since, hostname, displayname, blockchain):
    result = None
    try:
        result = db.session.query(Alert).filter(
                or_(Alert.hostname==hostname,Alert.hostname==displayname), 
                Alert.blockchain==blockchain,
                Alert.created_at >= since,
                Alert.priority == "LOW",
                Alert.service == "DAILY"
            ).order_by(Alert.created_at.desc()).first()
        #app.logger.info("Daily for {0}-{1} is {2}".format(displayname, blockchain, result))
        if result:
            return result.message
    except Exception as ex:
        app.logger.info("Failed to query for latest daily summary for {0} - {1} because {2}".format(
            hostname, blockchain, str(ex)))
    return result

def load_recent_disk_usage(disk_type):
    db = get_stats_db()
    cur = db.cursor()
    summary_by_worker = {}
    value_factor = "" # Leave at GB for plotting disks
    if disk_type == "plots":
        value_factor = "/1024"  # Divide to TB for plots disks
    for host in chia.load_farmers():
        hostname = host.hostname
        dates = []
        paths = {}
        sql = "select path, value{0}, created_at from stat_{1}_disk_used where (hostname = ? or hostname = ?) order by created_at, path".format(value_factor, disk_type)
        used_result = cur.execute(sql, [ host.hostname, host.displayname, ]).fetchall()
        for used_row in used_result:
            converted_date = converters.convert_date_for_luxon(used_row[2])
            if not converted_date in dates:
                dates.append(converted_date)
            if not used_row[0] in paths:
                paths[used_row[0]] = {}
            values = paths[used_row[0]]
            values[converted_date] = used_row[1]
        if len(dates) > 0:
            summary_by_worker[hostname] = { "dates": dates, "paths": paths.keys(),  }
            for path in paths.keys():
                path_values = []
                for date in dates:
                    if path in paths:
                        path_values.append(paths[path][date])
                    else:
                        path_values.append('null')
                summary_by_worker[hostname][path] = path_values
    app.logger.debug(summary_by_worker.keys())
    return summary_by_worker

def load_current_disk_usage(disk_type, hostname=None):
    db = get_stats_db()
    cur = db.cursor()
    summary_by_worker = {}
    value_factor = "" # Leave at GB for plotting disks
    if disk_type == "plots":
        value_factor = "/1024"  # Divide to TB for plots disks
    for host in chia.load_farmers():
        if hostname and not (hostname == host.hostname or hostname == host.displayname):
            continue
        paths = []
        used = []
        free = []
        sql = "select path, value{0}, created_at from stat_{1}_disk_used where (hostname = ? or hostname = ?) group by path having max(created_at)".format(value_factor, disk_type)
        used_result = cur.execute(sql, [ host.hostname, host.displayname, ]).fetchall()
        sql = "select path, value{0}, created_at from stat_{1}_disk_free where (hostname = ? or hostname = ?) group by path having max(created_at)".format(value_factor, disk_type)
        free_result =cur.execute(sql, [ host.hostname, host.displayname, ]).fetchall()
        if len(used_result) != len(free_result):
            app.logger.debug("Found mismatched count of disk used/free stats for {0}".format(disk_type))
        else:
            for used_row in used_result:
                paths.append(used_row[0])
                used.append(used_row[1])
                for free_row in free_result:
                    if used_row[0] == free_row[0]:
                        free.append(free_row[1])
                        continue
            if len(paths):
                summary_by_worker[host.hostname] = { "paths": paths, "used": used, "free": free}
    #app.logger.debug(summary_by_worker.keys())
    return summary_by_worker

def prune_workers_status(hostname, displayname, blockchain):
    try:
        db = get_stats_db()
        cur = db.cursor()
        for table in ALL_TABLES_BY_HOSTNAME:
            cur.execute("DELETE FROM " + table + " WHERE (hostname = :hostname OR hostname = :displayname)", 
                {"hostname":hostname, "displayname":displayname})
        db.commit()
    except Exception as ex:
        app.logger.info("Failed to remove stale stats for worker {0} - {1} because {2}".format(displayname, blockchain, str(ex)))
