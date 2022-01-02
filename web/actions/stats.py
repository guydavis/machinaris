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
from common.models.plots import Plot
from common.models.stats import StatPlotCount, StatPlotsSize, StatTotalCoins, StatNetspaceSize, StatTimeToWin, \
        StatPlotsTotalUsed, StatPlotsDiskUsed, StatPlotsDiskFree, StatPlottingTotalUsed, \
        StatPlottingDiskUsed, StatPlottingDiskFree
from web import app, db, utils
from web.actions import chia, worker

ALL_TABLES_BY_HOSTNAME = [
    StatPlotsDiskUsed,
    StatPlottingDiskUsed,
    StatPlotsDiskFree,
    StatPlottingDiskFree,
]

def load_daily_diff(farm_summary):
    for blockchain in farm_summary.farms:
        summary = {}
        # initialize defaults
        since_date = datetime.datetime.now() - datetime.timedelta(hours=24)
        since_str = since_date.strftime("%Y%m%d%H%M%S")
        summary['plot_count'] = plot_count_diff(since_str, blockchain)
        summary['plots_size'] = plots_size_diff(since_str, blockchain)
        summary['total_coin'] = total_coin_diff(since_str, blockchain)
        summary['netspace_size'] = netspace_size_diff(since_str, blockchain)
        #app.logger.info("{0} -> {1}".format(blockchain, summary))
        farm_summary.farms[blockchain]['daily_diff'] = summary

def plot_count_diff(since, blockchain):
    result = ''
    try:
        latest = db.session.query(StatPlotCount).filter(StatPlotCount.blockchain==blockchain).order_by(StatPlotCount.created_at.desc()).limit(1).first()
        #app.logger.info(latest.value)
        before = db.session.query(StatPlotCount).filter(StatPlotCount.blockchain==blockchain, StatPlotCount.created_at <= since).order_by(StatPlotCount.created_at.desc()).limit(1).first()
        #app.logger.info(before.value)
        if (latest.value - before.value) != 0:
            result = "%+0g in last day." % (latest.value - before.value)
    except Exception as ex:
        app.logger.debug("Failed to query for day diff of plot_count because {0}".format(str(ex)))
    #app.logger.info("Result is: {0}".format(result))
    return result

def plots_size_diff(since, blockchain):
    result = ''
    try:
        latest = db.session.query(StatPlotsSize).filter(StatPlotsSize.blockchain==blockchain).order_by(StatPlotsSize.created_at.desc()).limit(1).first()
        #app.logger.info(latest.value)
        before = db.session.query(StatPlotsSize).filter(StatPlotsSize.blockchain==blockchain, StatPlotsSize.created_at <= since).order_by(StatPlotsSize.created_at.desc()).limit(1).first()
        #app.logger.info(before.value)
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
    #app.logger.info("Result is: {0}".format(result))
    return result

def total_coin_diff(since, blockchain):
    result = ''
    try:
        latest = db.session.query(StatTotalCoins).filter(StatTotalCoins.blockchain==blockchain).order_by(StatTotalCoins.created_at.desc()).limit(1).first()
        #app.logger.info(latest.value)
        before = db.session.query(StatTotalCoins).filter(StatTotalCoins.blockchain==blockchain, StatTotalCoins.created_at <= since).order_by(StatTotalCoins.created_at.desc()).limit(1).first()
        #app.logger.info(before.value)
        if (latest.value - before.value) != 0:
            result = "%+6g in last day." % (latest.value - before.value)
    except Exception as ex:
        app.logger.debug("Failed to query for day diff of total_coin because {0}".format(str(ex)))
    #app.logger.info("Result is: {0}".format(result))
    return result

def netspace_size_diff(since, blockchain):
    result = ''
    try:
        latest = db.session.query(StatNetspaceSize).filter(StatNetspaceSize.blockchain==blockchain).order_by(StatNetspaceSize.created_at.desc()).limit(1).first()
        #app.logger.info(latest.value)
        before = db.session.query(StatNetspaceSize).filter(StatNetspaceSize.blockchain==blockchain, StatNetspaceSize.created_at <= since).order_by(StatNetspaceSize.created_at.desc()).limit(1).first()
        #app.logger.info(before.value)
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
            summary_by_workers[host.displayname][wk['blockchain']] = daily_summaries(since_date, wk['hostname'], wk['displayname'], wk['blockchain']) 
            #app.logger.info("{0}-{1}: {2}".format(short_name, wk['blockchain'], summary_by_workers[short_name][wk['blockchain']]))
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
    summary_by_worker = {}
    for host in worker.load_workers():
        hostname = host.hostname
        dates = []
        paths = {}
        if disk_type == 'plots':
            used_result = db.session.query(StatPlotsDiskUsed).filter( 
                or_(StatPlotsDiskUsed.hostname == host.hostname, StatPlotsDiskUsed.hostname == host.displayname)). \
                order_by(StatPlotsDiskUsed.created_at, StatPlotsDiskUsed.path).all()
        elif disk_type == 'plotting':
            used_result = db.session.query(StatPlottingDiskUsed).filter( 
                or_(StatPlottingDiskUsed.hostname == host.hostname, StatPlottingDiskUsed.hostname == host.displayname)). \
                order_by(StatPlottingDiskUsed.created_at, StatPlottingDiskUsed.path).all()
        else:
            raise Exception("Unknown disk type provided.")
        for used_row in used_result:
            converted_date = converters.convert_date_for_luxon(used_row.created_at)
            if not converted_date in dates:
                dates.append(converted_date)
            if not used_row.path in paths:
                paths[used_row.path] = {}
            values = paths[used_row.path]
            values[converted_date] = used_row.value
        if len(dates) > 0:
            summary_by_worker[hostname] = { "dates": dates, "paths": paths.keys(),  }
            for path in paths.keys():
                path_values = []
                for date in dates:
                    if path in paths:
                        if date in paths[path]:
                            if disk_type == "plots":  
                                path_values.append(paths[path][date] / 1024) # Convert to TB
                            else:
                                path_values.append(paths[path][date]) # Leave at GB
                        else: # Due to exeception reported by one user
                            path_values.append('null')
                    else:
                        path_values.append('null')
                summary_by_worker[hostname][path] = path_values
    app.logger.debug(summary_by_worker.keys())
    return summary_by_worker

def load_current_disk_usage(disk_type, hostname=None):
    summary_by_worker = {}
    for host in worker.load_workers():
        if hostname and not (hostname == host.hostname or hostname == host.displayname):
            continue
        paths = []
        used = []
        free = []
        if disk_type == 'plots':
            created_at_max = db.session.query(StatPlotsDiskUsed).order_by(StatPlotsDiskUsed.created_at.desc()).first()
            used_result = db.session.query(StatPlotsDiskUsed).filter( 
                or_(StatPlotsDiskUsed.hostname == host.hostname, StatPlotsDiskUsed.hostname == host.displayname),
                    StatPlotsDiskUsed.created_at == created_at_max.created_at).order_by(StatPlotsDiskUsed.path).all()
            free_result = db.session.query(StatPlotsDiskFree).filter( 
                or_(StatPlotsDiskFree.hostname == host.hostname, StatPlotsDiskFree.hostname == host.displayname),
                    StatPlotsDiskFree.created_at == created_at_max.created_at).order_by(StatPlotsDiskFree.path).all()
        elif disk_type == 'plotting':
            created_at_max = db.session.query(StatPlottingDiskUsed).order_by(StatPlottingDiskUsed.created_at.desc()).first()
            used_result = db.session.query(StatPlottingDiskUsed).filter( 
                or_(StatPlottingDiskUsed.hostname == host.hostname, StatPlottingDiskUsed.hostname == host.displayname),
                    StatPlottingDiskUsed.created_at == created_at_max.created_at).order_by(StatPlottingDiskUsed.path).all()
            free_result = db.session.query(StatPlottingDiskFree).filter( 
                or_(StatPlottingDiskFree.hostname == host.hostname, StatPlottingDiskFree.hostname == host.displayname),
                    StatPlottingDiskFree.created_at == created_at_max.created_at).order_by(StatPlottingDiskFree.path).all()
        else:
            raise Exception("Unknown disk type provided.")
        #sql = "select path, value{0}, created_at from stat_{1}_disk_used where (hostname = ? or hostname = ?) group by path having max(created_at)".format(value_factor, disk_type)
        #used_result = db.engine.execute(sql, [ host.hostname, host.displayname, ]).fetchall()
        #sql = "select path, value{0}, created_at from stat_{1}_disk_free where (hostname = ? or hostname = ?) group by path having max(created_at)".format(value_factor, disk_type)
        #free_result =cur.execute(sql, [ host.hostname, host.displayname, ]).fetchall()
        if len(used_result) != len(free_result):
            app.logger.info("Found mismatched count of disk used/free stats for {0}".format(disk_type))
        else:
            for used_row in used_result:
                paths.append(used_row.path)
                if disk_type == "plots":  
                    used.append(used_row.value / 1024) # Convert to TB
                else:
                    used.append(used_row.value) # Leave at GB
                for free_row in free_result:
                    if used_row.path == free_row.path:
                        if disk_type == "plots":  
                            free.append(free_row.value / 1024) # Convert to TB
                        else:
                            free.append(free_row.value) # Leave at GB
                        continue
            if len(paths):
                summary_by_worker[host.hostname] = { "paths": paths, "used": used, "free": free}
    #app.logger.debug(summary_by_worker.keys())
    return summary_by_worker

def prune_workers_status(hostname, displayname, blockchain):
    try:
        for table in ALL_TABLES_BY_HOSTNAME:
            db.session.query(table).filter(or_((table.hostname == hostname), (table.hostname == worker.displayname)), table.blockchain == worker.blockchain).delete()
            db.session.commit()
    except Exception as ex:
        app.logger.info("Failed to remove stale stats for worker {0} - {1} because {2}".format(displayname, blockchain, str(ex)))

def load_plotting_stats():
    summary_by_size = {}
    for k in [29, 30, 31, 32, 33, 34]:  # Current k sizes
        dates = []
        workers = {}
        result = db.session.query(Plot).order_by(Plot.created_at.desc()).filter(
                Plot.plot_analyze != '-',
                Plot.plot_analyze.is_not(None),
                Plot.file.like('%-k{0}-%'.format(k)),
            ).limit(100).all()
        for p in result:
            converted_date = p.created_at.replace(' ', 'T') # Change space between date & time to 'T' for luxon
            if not converted_date in dates:
                dates.append(converted_date)
            if not p.displayname in workers:
                workers[p.displayname] = {}
            values = workers[p.displayname]
            try:
                values[converted_date] = round(float(p.plot_analyze) / 60, 2) # Convert from seconds to minutes
            except:
                app.logger.error("Inavlid plot_analyze time in seconds: {0}".format(p.plot_analyze))
                values[converted_date] = 'null'
        if len(dates) > 0:
            summary_by_size[k] = { "dates": dates, "workers": workers.keys(),  }
            for worker in workers.keys():
                worker_values = []
                for date in dates:
                    if worker in workers:
                        if date in workers[worker]:  
                            worker_values.append(workers[worker][date])
                        else: # Due to exeception reported by one user
                            worker_values.append('null')
                    else:
                        worker_values.append('null')
                summary_by_size[k][worker] = worker_values
    #app.logger.info(summary_by_size.keys())
    return summary_by_size
