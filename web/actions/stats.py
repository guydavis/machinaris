#
# Access to statistics and calculated values.
#

import datetime
import os
import pathlib
import random
import sqlite3
import time

from flask import g
from sqlalchemy import or_, func
from shutil import disk_usage
from flask_babel import _, lazy_gettext as _l, format_decimal

from common.config import globals
from common.utils import converters, fiat
from common.models.alerts import Alert
from common.models.challenges import Challenge
from common.models.drives import Drive
from common.models.farms import Farm
from common.models.pools import POOLABLE_BLOCKCHAINS
from common.models.plots import Plot
from common.models.pools import Pool
from common.models.partials import Partial
from common.models.stats import StatPlotCount, StatPlotsSize, StatTotalCoins, StatNetspaceSize, StatTimeToWin, \
        StatPlotsTotalUsed, StatPlotsDiskUsed, StatPlotsDiskFree, StatPlottingTotalUsed, StatEffort, \
        StatPlottingDiskUsed, StatPlottingDiskFree, StatFarmedBlocks, StatWalletBalances, StatTotalBalance, \
        StatContainerMemoryUsageGib, StatHostMemoryUsagePercent
from web import app, db, utils
from web.actions import chia, worker

ALL_TABLES_BY_HOSTNAME = [
    StatPlotsDiskUsed,
    StatPlottingDiskUsed,
    StatPlotsDiskFree,
    StatPlottingDiskFree,
]

# Don't overload the bar chart with tons of plots paths, randomly sample only this amount
MAX_ALLOWED_PATHS_ON_BAR_CHART = 20

def load_daily_diff(farm_summary):
    for blockchain in farm_summary.farms:
        summary = {}
        # initialize defaults
        since_date = datetime.datetime.now() - datetime.timedelta(hours=24)
        since_str = since_date.strftime("%Y%m%d%H%M%S")
        summary['plot_count'] = plot_count_diff(since_str, blockchain).strip()
        summary['plots_size'] = plots_size_diff(since_str, blockchain).strip()
        if upgrade_marker_at_least_day_old():  # Guard against spurious notification
            summary['total_coins'] = total_coin_diff(since_str, blockchain).strip()
        summary['wallet_balance'] = wallet_balance_diff(since_str, blockchain).strip()
        summary['netspace_size'] = netspace_size_diff(since_str, blockchain).strip()
        #app.logger.info("{0} -> {1}".format(blockchain, summary))
        farm_summary.farms[blockchain]['daily_diff'] = summary

# On upgrade to v0.8.0, farming directly to cold_wallet started to be tracked.
# To avoid a spurious notification immediatly upon upgrading, use marker file that must be at least a day old
def upgrade_marker_at_least_day_old():
    if os.path.exists('/root/.chia/machinaris/tmp/total_coins_upgrade.tmp'):
        day_ago = datetime.datetime.now() - datetime.timedelta(days=1)
        if os.path.getctime('/root/.chia/machinaris/tmp/total_coins_upgrade.tmp') <= day_ago.timestamp():
            app.logger.debug("Total coins upgrade indicates past 24 hours since upgrade.")
            return True
        else:
            app.logger.debug("Total coins upgrade indicates less than 24 hours since upgrade.")
    else:
        pathlib.Path('/root/.chia/machinaris/tmp/').mkdir(parents=True, exist_ok=True)
        pathlib.Path('/root/.chia/machinaris/tmp/total_coins_upgrade.tmp').touch()
        app.logger.debug("Total coins upgrade just occured.  24 hours until a new total coin value diff generated.")
    return False

def plot_count_diff(since, blockchain):
    result = ''
    try:
        latest = db.session.query(StatPlotCount).filter(StatPlotCount.blockchain==blockchain).order_by(StatPlotCount.created_at.desc()).limit(1).first()
        #app.logger.info(latest.value)
        before = db.session.query(StatPlotCount).filter(StatPlotCount.blockchain==blockchain, StatPlotCount.created_at <= since).order_by(StatPlotCount.created_at.desc()).limit(1).first()
        #app.logger.info(before.value)
        if (latest and before) and (latest.value - before.value) != 0:
            result = ("%+0g " % (latest.value - before.value)) + _('in last day.')
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
        if (latest and before):
            gibs = (latest.value - before.value)
            fmtted = converters.gib_to_fmt(gibs)
            if fmtted == "0 B":
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
        if (latest and before) and (latest.value - before.value) != 0:
            result = ("%+6g " % (latest.value - before.value)) + _('in last day.')
            #app.logger.info("Total coins daily diff: {0}".format(result))
    except Exception as ex:
        app.logger.debug("Failed to query for day diff of total_coin because {0}".format(str(ex)))
    #app.logger.info("Result is: {0}".format(result))
    return result

def wallet_balance_diff(since, blockchain):
    result = ''
    try:
        latest = db.session.query(StatWalletBalances).filter(StatWalletBalances.blockchain==blockchain).order_by(StatWalletBalances.created_at.desc()).limit(1).first()
        before = db.session.query(StatWalletBalances).filter(StatWalletBalances.blockchain==blockchain, StatWalletBalances.created_at <= since).order_by(StatWalletBalances.created_at.desc()).limit(1).first()
        if (latest and before) and (latest.value - before.value) != 0:
            result = ("%+6g " % (latest.value - before.value)) + _('in last day.')
            #app.logger.info("Total coins daily diff: {0}".format(result))
    except Exception as ex:
        app.logger.info("Failed to query for day diff of wallet_balances because {0}".format(str(ex)))
    #app.logger.info("Result is: {0}".format(result))
    return result

def netspace_size_diff(since, blockchain):
    result = ''
    try:
        latest = db.session.query(StatNetspaceSize).filter(StatNetspaceSize.blockchain==blockchain).order_by(StatNetspaceSize.created_at.desc()).limit(1).first()
        #app.logger.info(latest.value)
        before = db.session.query(StatNetspaceSize).filter(StatNetspaceSize.blockchain==blockchain, StatNetspaceSize.created_at <= since).order_by(StatNetspaceSize.created_at.desc()).limit(1).first()
        #app.logger.info(before.value)
        if (latest and before):
            gibs = (latest.value - before.value)
            fmtted = converters.gib_to_fmt(gibs)
            if fmtted == "0 B":
                result = ""
            elif not fmtted.startswith('-'):
                result = ("+{0} ".format(fmtted))  + _('in last day.')
            else:
                result = ("{0} ".format(fmtted)) + _('in last day.')
    except Exception as ex:
        app.logger.debug("Failed to query for day diff of netspace_size because {0}".format(str(ex)))
    #app.logger.info("Result is: {0}".format(result))
    return result

def load_daily_farming_summaries(farmers):
    summary_by_workers = {}
    since_date = datetime.datetime.now() - datetime.timedelta(hours=24)
    for host in farmers:
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
    return summary_by_worker

def load_current_disk_usage(disk_type, hostname=None):
    summary_by_worker = {}
    for host in worker.load_workers():
        if hostname and not (hostname == host.hostname or hostname == host.displayname):
            continue
        paths = []
        used = []
        free = []
        used_result = free_result = None
        if disk_type == 'plots':
            created_at_max = db.session.query(StatPlotsDiskUsed).order_by(StatPlotsDiskUsed.created_at.desc()).first()
            if created_at_max:
                used_result = db.session.query(StatPlotsDiskUsed).filter( 
                    or_(StatPlotsDiskUsed.hostname == host.hostname, StatPlotsDiskUsed.hostname == host.displayname),
                        StatPlotsDiskUsed.created_at == created_at_max.created_at).order_by(StatPlotsDiskUsed.path).all()
                free_result = db.session.query(StatPlotsDiskFree).filter( 
                    or_(StatPlotsDiskFree.hostname == host.hostname, StatPlotsDiskFree.hostname == host.displayname),
                        StatPlotsDiskFree.created_at == created_at_max.created_at).order_by(StatPlotsDiskFree.path).all()
        elif disk_type == 'plotting':
            created_at_max = db.session.query(StatPlottingDiskUsed).order_by(StatPlottingDiskUsed.created_at.desc()).first()
            if created_at_max:
                used_result = db.session.query(StatPlottingDiskUsed).filter( 
                    or_(StatPlottingDiskUsed.hostname == host.hostname, StatPlottingDiskUsed.hostname == host.displayname),
                        StatPlottingDiskUsed.created_at == created_at_max.created_at).order_by(StatPlottingDiskUsed.path).all()
                free_result = db.session.query(StatPlottingDiskFree).filter( 
                    or_(StatPlottingDiskFree.hostname == host.hostname, StatPlottingDiskFree.hostname == host.displayname),
                        StatPlottingDiskFree.created_at == created_at_max.created_at).order_by(StatPlottingDiskFree.path).all()
        else:
            raise Exception("Unknown disk type provided.")
        if not used_result or not free_result:
            app.logger.info("Found no {0} disk usage stats.".format(disk_type))
        elif len(used_result) != len(free_result):
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
                if len(paths) > MAX_ALLOWED_PATHS_ON_BAR_CHART:
                    paths = sorted(random.sample(paths, MAX_ALLOWED_PATHS_ON_BAR_CHART))
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
    worker_ips_to_displaynames = {}
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
            if '|' in p.plot_analyze:
                [worker_hostname, analyze_seconds] = p.plot_analyze.split('|')
                if worker_hostname in worker_ips_to_displaynames:
                    worker_displayname = worker_ips_to_displaynames[worker_hostname]
                else:
                    try:
                        worker_displayname = worker.get_worker(worker_hostname).displayname # Convert ip_addr to worker displayname
                        worker_ips_to_displaynames[worker_hostname] = worker_displayname
                    except Exception as ex:
                        app.logger.info("Unable to convert {0} to a worker's displayname because: {1}".format(worker_hostname, str(ex)))
                        worker_displayname = p.displayname  # Pretend plot host was also the plotter
            else: # Old format, just seconds
                analyze_seconds =  p.plot_analyze
                worker_displayname = p.displayname  # Pretend plot host was also the plotter
            if not worker_displayname in workers:
                workers[worker_displayname] = {}
            values = workers[worker_displayname]
            try:
                values[converted_date] = round(float(analyze_seconds) / 60, 2) # Convert from seconds to minutes
            except:
                app.logger.error("Inavlid plot_analyze time found in ip_addr|seconds: {0}".format(p.plot_analyze))
                values[converted_date] = 'null'
        if len(dates) > 0:
            summary_by_size[k] = { "dates": dates, "workers": sorted(workers.keys()),  }
            for wkr in workers.keys():
                worker_values = []
                for date in dates:
                    if wkr in workers:
                        if date in workers[wkr]:  
                            worker_values.append(workers[wkr][date])
                        else: # Due to exeception reported by one user
                            worker_values.append('null')
                    else:
                        worker_values.append('null')
                summary_by_size[k][wkr] = worker_values
    #app.logger.info(summary_by_size.keys())
    return summary_by_size

def get_current_effort(blockchain):
    effort = ''
    try:
        result = db.session.query(StatEffort).filter(StatEffort.blockchain == blockchain).order_by(StatEffort.created_at.desc()).first()
        if result:
            effort = "{:.0f}%".format(result.value) # Round to zero as this is a percentage
    except Exception as ex:
        app.logger.info("Failed to query effort for {0} because {1}".format(blockchain, str(ex)))
    #app.logger.info("Effort on {0} is {1}".format(blockchain, effort))
    return effort

def calc_estimated_daily_value(blockchain):
    edv = None
    edv_fiat = None
    result = []
    try:
        farm = db.session.query(Farm).filter(Farm.blockchain == blockchain).first()
        blocks_per_day = globals.get_blocks_per_day(blockchain)
        if blockchain == 'mmx': # Uses a dynamic reward
            block_reward = worker.mmx_block_reward()
        else: # All Chia blockchains use a regular reward
            block_reward = globals.get_block_reward(blockchain)
        symbol = globals.get_blockchain_symbol(blockchain).lower()
        if block_reward and farm.netspace_size > 0:
            edv = blocks_per_day * block_reward * farm.plots_size / farm.netspace_size
    except Exception as ex:
        app.logger.info("Failed to calculate EDV for {0} because {1}".format(blockchain, str(ex)))
    if edv and farm.status == 'Farming': # Don't calculate EDV if not fully synced
        if edv >= 1000:
            result.append("{0} {1}".format(format_decimal(round(edv, 0)), symbol))
        else:
            result.append("{0} {1}".format(format_decimal(round(edv, 3)), symbol))
    else:
        result.append('')
    if edv and farm.status == 'Farming': # Don't calculate EDV if not fully synced:
        try:
            edv_fiat = fiat.to_fiat(blockchain, edv)
        except Exception as ex:
            app.logger.info("Failed to calculate edv_fiat for {0} because {1}".format(blockchain, str(ex)))
        result.append(edv_fiat)
    else:
        result.append('')
    return result

def load_summary_stats(blockchains):
    all_farmers = worker.load_worker_summary().farmers_harvesters()
    stats = {}
    for b in blockchains:
        blockchain = b['blockchain']
        harvesters = ''
        try:
            harvsters_online = 0
            harvesters_total = 0
            for host in all_farmers:
                for wk in host.workers:
                    if wk['blockchain'] == blockchain:
                        harvesters_total += 1
                        #app.logger.info(wk['farming_status'])
                        if wk['farming_status'] in ['farming', 'harvesting']: 
                            harvsters_online += 1
            harvesters = "{0} / {1}".format(harvsters_online, harvesters_total)
        except Exception as ex:
            app.logger.error(ex)
            app.logger.info("No recent challenge response times found for {0}".format(blockchain))
        max_response = ''
        try:
            max_record = db.session.query(Challenge).filter(Challenge.blockchain==blockchain).order_by(Challenge.time_taken.desc()).first()
            if max_record:  # Strip of 'secs' unit before rounding
                max_response = "{0} {1}".format(format_decimal(round(float(max_record.time_taken.split()[0]),2)), _('secs'))
        except Exception as ex:
            app.logger.error(ex)
            app.logger.info("No recent challenge response times found for {0}".format(blockchain))
        partials_per_hour = ''
        if blockchain in POOLABLE_BLOCKCHAINS:
            if len(db.session.query(Pool).filter(Pool.blockchain==blockchain).all()) > 0:
                try:
                    day_ago = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d %H:%M")
                    partial_records = db.session.query(Partial).filter(Partial.blockchain==blockchain, Partial.created_at >= day_ago ).order_by(Partial.created_at.desc()).all()
                    partials_per_hour = "{0} / {1}".format(format_decimal(round(len(partial_records)/24,2)), _('hour'))
                except Exception as ex:
                    app.logger.error(ex)
                    app.logger.info("No recent partials submitted for {0}".format(blockchain))
        [edv, edv_fiat] = calc_estimated_daily_value(blockchain)
        stats[blockchain] = {
            'harvesters': harvesters,
            'max_resp': max_response,
            'partials_per_hour': partials_per_hour,
            'edv': edv,
            'edv_fiat': edv_fiat,
            'effort':  get_current_effort(blockchain)
        }
    return stats

def load_farmed_coins(blockchain):
    dates = []
    values = []
    result = db.session.query(StatTotalCoins).order_by(StatTotalCoins.created_at.asc()).filter(
            StatTotalCoins.blockchain == blockchain).all()
    last_value = None
    for i in range(len(result)):
        s = result[i]
        converted_date = converters.convert_date_for_luxon(s.created_at)
        if (last_value != s.value) or (i % 24 == 0) or (i == len(result) - 1):
            dates.append(converted_date)
            values.append(s.value)
            last_value = s.value
    #app.logger.info(dates)
    #app.logger.info(values)
    return { 'title': blockchain.capitalize() + ' - ' + _('Farmed Coins'), 'dates': dates, 'vals': values}

def load_wallet_balances(blockchain):
    dates = []
    values = []
    result = db.session.query(StatWalletBalances).order_by(StatWalletBalances.created_at.asc()).filter(
            StatWalletBalances.blockchain == blockchain).all()
    last_value = None
    for i in range(len(result)):
        s = result[i]
        converted_date = converters.convert_date_for_luxon(s.created_at)
        if (last_value != s.value) or ((i + 12) % 24 == 0) or (i == len(result) - 1):
            dates.append(converted_date)
            values.append(s.value)
            last_value = s.value
    #app.logger.info(dates)
    #app.logger.info(values)
    return { 'title': blockchain.capitalize() + ' - ' + _('Total Balance'), 'dates': dates, 'vals': values}

def load_total_balances(current_currency_symbol):
    dates = []
    values = []
    result = db.session.query(StatTotalBalance).order_by(StatTotalBalance.created_at.asc()).filter(
            StatTotalBalance.currency==current_currency_symbol).all()
    last_value = None
    for i in range(len(result)):
        s = result[i]
        converted_date = converters.convert_date_for_luxon(s.created_at)
        if (last_value != s.value) or ((i + 12) % 24 == 0) or (i == len(result) - 1):
            dates.append(converted_date)
            values.append(s.value)
            last_value = s.value
    #app.logger.info(dates)
    #app.logger.info(values)
    return { 'title': _('Wallets Total') + ' (' + current_currency_symbol + ')', 'y_axis_title': _('Fiat Currency'),
         'dates': dates, 'vals': values, 'last_value': " - {0} {1}".format(last_value, current_currency_symbol) }

def load_host_memory_usage():
    dates = []
    workers = {}
    displaynames_for_hosts = {}
    result = db.session.query(StatHostMemoryUsagePercent).order_by(StatHostMemoryUsagePercent.created_at.asc()).all()
    for p in result:
        converted_date = converters.convert_date_for_luxon(p.created_at)
        if not converted_date in dates:
            dates.append(converted_date)
        if p.hostname in displaynames_for_hosts:
            displayname = displaynames_for_hosts[p.hostname]
        else:
            try:
                w = worker.get_worker(p.hostname)
                displayname = w.displayname
            except:
                app.logger.debug("Failed to find worker for hostname: {0}".format(p.hostname))
                displayname = p.hostname
        if not displayname in workers:
            workers[displayname] = {}
        values = workers[displayname]
        values[converted_date] = p.value # Integer as percent of all host memory used
    values_per_worker = {}
    if len(dates) > 0:
        for wk in workers.keys():
            worker_values = []
            for date in dates:
                if wk in workers:
                    if date in workers[wk]:  
                        worker_values.append(str(workers[wk][date]))
                    else: # Due to exeception reported by one user
                        worker_values.append('null')
                else:
                    worker_values.append('null')
            values_per_worker[wk] = worker_values
    #app.logger.info(dates)
    #app.logger.info(values_per_worker)
    return {'y_axis_title': _('Host Memory Usage') + ' (%)',
         'dates': dates, "workers": workers.keys(), "values_per_worker": values_per_worker }

def load_netspace_size(blockchain):
    dates = []
    values = []
    result = db.session.query(StatNetspaceSize).order_by(StatNetspaceSize.created_at.asc()).filter(
            StatNetspaceSize.blockchain == blockchain).all()
    for i in range(len(result)):
        s = result[i]
        converted_date = converters.convert_date_for_luxon(s.created_at)
        if (i == 0) or (i % 24 == 0) or (i == len(result) - 1):
            dates.append(converted_date)
            values.append(s.value)
    if len(values) > 0:
        unit = converters.gib_to_fmt(max(values)).split()[1]
        converted_values = list(map(lambda x: converters.gib_to_float(x, unit), values))
    else:
        unit = 'B'
        converted_values = []
    return { 'title': blockchain.capitalize() + ' - ' + _('Netspace Size'), 'dates': dates, 'vals': converted_values, 
        'y_axis_title': _('Size') + ' (' + unit + ')'}

def load_farmed_blocks(blockchain):
    blocks = []
    result = db.session.query(StatFarmedBlocks).order_by(StatFarmedBlocks.created_at.desc()).filter(
            StatFarmedBlocks.blockchain == blockchain).all()
    for row in result:
        try:
            w = worker.get_worker(row.hostname)
            displayname = w.displayname
        except:
            app.logger.debug("Failed to find worker for hostname: {0}".format(w.hostname))
            displayname = row.hostname
        blocks.append({
            'hostname': displayname,
            'blockchain': blockchain,
            'created_at': row.created_at,
            'farmed_block': row.farmed_block,
            'plot_files': row.plot_files, 
        })
    #app.logger.info(blocks)
    return blocks

def load_plot_count(blockchain):
    dates = []
    values = []
    result = db.session.query(StatPlotCount).order_by(StatPlotCount.created_at.asc()).filter(
            StatPlotCount.blockchain == blockchain).all()
    last_value = None
    for i in range(len(result)):
        s = result[i]
        converted_date = converters.convert_date_for_luxon(s.created_at)
        if (last_value != s.value) or (i % 24 == 0) or (i == len(result) - 1):
            dates.append(converted_date)
            values.append(s.value)
            last_value = s.value
    #app.logger.info(dates)
    #app.logger.info(values)
    return { 'title': blockchain.capitalize() + ' - ' + _('Plot Counts'), 'dates': dates, 'vals': values}

def load_plots_size(blockchain):
    dates = []
    values = []
    result = db.session.query(StatPlotsSize).order_by(StatPlotsSize.created_at.asc()).filter(
            StatPlotsSize.blockchain == blockchain).all()
    last_value = None
    for i in range(len(result)):
        s = result[i]
        converted_date = converters.convert_date_for_luxon(s.created_at)
        if (last_value != s.value) or (i % 24 == 0) or (i == len(result) - 1):
            dates.append(converted_date)
            values.append(s.value)
            last_value = s.value
    if len(values) > 0:
        unit = converters.gib_to_fmt(max(values)).split()[1]
        converted_values = list(map(lambda x: converters.gib_to_float(x, unit), values))
    else:
        unit = 'B'
        converted_values = []
    return { 'title': blockchain.capitalize() + ' - ' + _('Plots Size'), 'dates': dates, 'vals': converted_values, 
        'y_axis_title': _('Size') + ' (' + unit + ')'}

def load_effort(blockchain):
    dates = []
    values = []
    result = db.session.query(StatEffort).order_by(StatEffort.created_at.asc()).filter(StatEffort.blockchain == blockchain).all()
    last_value = None
    for i in range(len(result)):
        s = result[i]
        converted_date = converters.convert_date_for_luxon(s.created_at)
        if (last_value != s.value) or (i % 24 == 0) or (i == len(result) - 1):
            dates.append(converted_date)
            values.append(s.value/100)
            last_value = s.value
    return { 'title': blockchain.capitalize() + ' - ' + _('Effort'), 'dates': dates, 'vals': values, 
        'y_axis_title': _('Effort')}

def wallet_chart_data(farm_summary):
    for blockchain in farm_summary.farms:
        balances = load_wallet_balances(blockchain)
        coins = load_farmed_coins(blockchain)
        chart_data = { 'dates': [], 'balances': [], 'coins': []}
        i = j = 0
        # First push thru wallet balances list
        while i < len(balances['dates']):
            balance_date = balances['dates'][i]
            if j < len(coins['dates']):
                coin_date = coins['dates'][j]
            else:
                coin_date = '2100-01-01' # far in future
            if balance_date < coin_date:
                chart_data['dates'].append(balance_date)
                chart_data['balances'].append(converters.round_balance_float(balances['vals'][i]))
                chart_data['coins'].append('null') # Javascript null
                i += 1
            else:
                chart_data['dates'].append(coin_date)
                chart_data['coins'].append(converters.round_balance_float(coins['vals'][j]))
                chart_data['balances'].append('null') # Javascript null
                j += 1
        # Then add any remaining farmed coins
        while j < len(coins['dates']):
            chart_data['dates'].append(coins['dates'][j])
            chart_data['coins'].append(converters.round_balance_float(coins['vals'][j]))
            chart_data['balances'].append('null') # Javascript null
            j += 1
        #app.logger.info("{0} -> {1}".format(blockchain, chart_data))
        farm_summary.farms[blockchain]['wallets'] = chart_data

def load_time_to_win(blockchain):
    dates = []
    values = []
    result = db.session.query(StatTimeToWin).order_by(StatTimeToWin.created_at.asc()).filter(
            StatTimeToWin.blockchain == blockchain).all()
    for i in range(len(result)):
        s = result[i]
        converted_date = converters.convert_date_for_luxon(s.created_at)
        if (i == 0) or (i % 24 == 0) or (i == len(result) - 1):
            dates.append(converted_date)
            values.append(s.value)
    app.logger.debug("{0} before {1}".format(blockchain, values))
    if len(values) > 0:
        converted_values = list(map(lambda x: round(x/60/24,2), values))  # Minutes to Days
    else:
        converted_values = []
    app.logger.debug("{0} after {1}".format(blockchain, converted_values))
    return { 'title': blockchain.capitalize() + ' - ' + _('ETW'), 'dates': dates, 'vals': converted_values, 
        'y_axis_title': _('Estimated Time to Win') + ' (' + _('days') + ')'}

def load_container_memory(hostname, blockchain):
    dates = []
    values = []
    result = db.session.query(StatContainerMemoryUsageGib).order_by(StatContainerMemoryUsageGib.created_at.asc()).filter(
            StatContainerMemoryUsageGib.hostname == hostname, StatContainerMemoryUsageGib.blockchain == blockchain).all()
    for i in range(len(result)):
        s = result[i]
        converted_date = converters.convert_date_for_luxon(s.created_at)
        # First, last, and every 5th (at ~2x5 min intervals)
        if (i == 0) or (i % 5 == 0) or (i == len(result) - 1):
            dates.append(converted_date)
            values.append(s.value)
    app.logger.debug("{0} before {1}".format(blockchain, values))
    if len(values) > 0:
        converted_values = list(map(lambda x: round(x/1024/1024/1024,2), values))  # Bytes to GiB
    else:
        converted_values = []
    app.logger.debug("{0} after {1}".format(blockchain, converted_values))
    try:
        displayname = worker.get_worker(hostname).displayname
    except:
        displayname = hostname
    return { 'title': blockchain.capitalize() + ' - ' + _('Container Memory Usage') +  ' - ' + displayname, 'dates': dates, 'vals': converted_values, 
        'y_axis_title': _('GiB') }

def count_plots_by_type(hostname):
    plots_by_type = {}
    result = db.session.query(Plot.type, func.count(Plot.hostname)).filter(Plot.hostname==hostname).group_by(Plot.type).all()
    for row in result:
        plots_by_type[row[0]] = str(row[1]) + " " + _('plots')
    return plots_by_type

def count_plots_by_ksize(hostname):
    plots_by_ksize = {}
    for ksize in [ "k29", "k30", "k31", "k32", "k33", "k34" ]:
        count = db.session.query(Plot.plot_id).filter(Plot.hostname==hostname, Plot.file.contains("-{0}-".format(ksize))).count()
        if count > 0:
            plots_by_ksize[ksize] = str(count) + " " + _('plots')
    return plots_by_ksize

def count_drives(hostname):
    return db.session.query(Drive.serial_number).filter(Drive.hostname==hostname).count()

def set_disk_usage_per_farmer(farmers, disk_usage):
    for farmer in farmers:
        if farmer.hostname in disk_usage:
            used = sum(disk_usage[farmer.hostname]['used'])
            free = sum(disk_usage[farmer.hostname]['free'])
            percent = used / (used + free) * 100
            farmer.drive_usage = "{0}% {1} ({2} TB of {3} TB). {4} TB {5}.".format(
                format_decimal(round(percent)),
                _('full'), 
                format_decimal(round(used)), 
                format_decimal(round(used + free)),
                format_decimal(round(free)),
                _('free')
            )
        else:
            app.logger.info("No disk usage stats found for {0}".format(farmer.hostname))
            farmer.drive_usage = "" # Empty string to report

def load_recent_mem_usage(worker_type, only_hostname=None, only_blockchain=None):
    summary_by_worker = {}
    for host in worker.load_workers():
        hostname = host.hostname
        if only_hostname and hostname != only_hostname:
            continue
        dates = []
        data_by_blockchain = {}
        if only_blockchain:
            mem_result = db.session.query(StatContainerMemoryUsageGib).filter( 
                StatContainerMemoryUsageGib.hostname == host.hostname, StatContainerMemoryUsageGib.blockchain == only_blockchain). \
                order_by(StatContainerMemoryUsageGib.created_at, StatContainerMemoryUsageGib.blockchain).all()
        else: # all blockchains on that hostname
            mem_result = db.session.query(StatContainerMemoryUsageGib).filter( 
                StatContainerMemoryUsageGib.hostname == host.hostname). \
                order_by(StatContainerMemoryUsageGib.created_at, StatContainerMemoryUsageGib.blockchain).all()
        for row in mem_result:
            if worker_type == 'plotting' and host.mode != 'plotter' and (host.mode == 'fullnode' and not row.blockchain in ['chia', 'chives', 'mmx']):
                continue  # Not a plotting container
            elif worker_type == 'farming' and host.mode == 'plotter':
                continue # Not a farmer or harvester
            converted_date = converters.convert_date_for_luxon(row.created_at)
            if not converted_date in dates:
                dates.append(converted_date)
            if not row.blockchain in data_by_blockchain:
                data_by_blockchain[row.blockchain] = {}
            data_by_blockchain[row.blockchain][converted_date] = round((row.value / 1024 / 1024 /1024), 2)
        if len(dates) > 0:
            summary_by_worker[hostname] = { "dates": dates, "blockchains": data_by_blockchain.keys(),  }
            for blockchain in data_by_blockchain.keys():
                blockchain_values = []
                for date in dates:
                    if blockchain in data_by_blockchain:
                        if date in data_by_blockchain[blockchain]:
                            blockchain_values.append(str(data_by_blockchain[blockchain][date]))
                        else: 
                            blockchain_values.append('null')
                    else:
                        blockchain_values.append('null')
                # TODO Decimate the memory usage datapoints as too many being returned...
                summary_by_worker[hostname][blockchain] = blockchain_values
    return summary_by_worker
