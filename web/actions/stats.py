#
# Access to statistics and calculated values.
#

import datetime
import sqlite3

from flask import g
from sqlalchemy import or_
from shutil import disk_usage
from flask_babel import _, lazy_gettext as _l, format_decimal

from common.config import globals
from common.utils import converters, fiat
from common.models.alerts import Alert
from common.models.challenges import Challenge
from common.models.farms import Farm
from common.models.pools import POOLABLE_BLOCKCHAINS
from common.models.plots import Plot
from common.models.pools import Pool
from common.models.partials import Partial
from common.models.stats import StatPlotCount, StatPlotsSize, StatTotalCoins, StatNetspaceSize, StatTimeToWin, \
        StatPlotsTotalUsed, StatPlotsDiskUsed, StatPlotsDiskFree, StatPlottingTotalUsed, \
        StatPlottingDiskUsed, StatPlottingDiskFree, StatFarmedBlocks, StatWalletBalances
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
        summary['total_coins'] = total_coin_diff(since_str, blockchain)
        summary['wallet_balance'] = wallet_balance_diff(since_str, blockchain)
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
        #if blockchain == 'cactus':
        #    app.logger.info(latest.value)
        before = db.session.query(StatWalletBalances).filter(StatWalletBalances.blockchain==blockchain, StatWalletBalances.created_at <= since).order_by(StatWalletBalances.created_at.desc()).limit(1).first()
        #if blockchain == 'cactus':
        #    app.logger.info(before.value)
        if (latest and before) and (latest.value - before.value) != 0:
            result = ("%+6g " % (latest.value - before.value)) + _('in last day.')
            #app.logger.info("Total coins daily diff: {0}".format(result))
    except Exception as ex:
        app.logger.info("Failed to query for day diff of wallet_balances because {0}".format(str(ex)))
    #if blockchain == 'cactus':
    #    app.logger.info("Result is: {0}".format(result))
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

def calc_estimated_daily_value(blockchain):
    edv = None
    edv_fiat = None
    result = []
    try:
        farm = db.session.query(Farm).filter(Farm.blockchain == blockchain).first()
        blocks_per_day = globals.get_blocks_per_day(blockchain)
        block_reward = globals.get_block_reward(blockchain)
        symbol = globals.get_blockchain_symbol(blockchain).lower()
        edv = blocks_per_day * block_reward * farm.plots_size / farm.netspace_size
    except Exception as ex:
        app.logger.info("Failed to calculate EDV for {0} because {1}".format(blockchain, str(ex)))
    if edv:
        if edv >= 1000:
            result.append("{0} {1}".format(format_decimal(round(edv, 0)), symbol))
        else:
            result.append("{0} {1}".format(format_decimal(round(edv, 3)), symbol))
    else:
        result.append('')
    try:
        edv_fiat = fiat.to_fiat(blockchain, edv)
    except Exception as ex:
        app.logger.info("Failed to calculate edv_fiat for {0} because {1}".format(blockchain, str(ex)))
    if edv:
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
                max_response = "{0} / {1}".format(format_decimal(round(float(max_record.time_taken.split()[0]),2)), _('secs'))
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
            'edv_fiat': edv_fiat
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
    #app.logger.info(dates)
    unit = converters.gib_to_fmt(max(values)).split()[1]
    converted_values = list(map(lambda x: float(converters.gib_to_fmt(x, target_unit=unit).split()[0]), values))
    #app.logger.info(converted_values)
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
            app.logger.debug("Failed to find worker for hostname: {0}".format(ResourceWarning.hostname))
            displayname = row.hostname
        blocks.append({
            'hostname': displayname,
            'blockchain': blockchain,
            'created_at': row.created_at,
            'farmed_block': row.farmed_block,
            'plot_files': row.plot_files, 
        })
    app.logger.info(blocks)
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
    #app.logger.info(dates)
    unit = converters.gib_to_fmt(max(values)).split()[1]
    converted_values = list(map(lambda x: float(converters.gib_to_fmt(x, target_unit=unit).split()[0]), values))
    #app.logger.info(converted_values)
    return { 'title': blockchain.capitalize() + ' - ' + _('Plots Size'), 'dates': dates, 'vals': converted_values, 
        'y_axis_title': _('Size') + ' (' + unit + ')'}

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
                chart_data['balances'].append(converters.round_balance(balances['vals'][i]))
                chart_data['coins'].append('null') # Javascript null
                i += 1
            else:
                chart_data['dates'].append(coin_date)
                chart_data['coins'].append(converters.round_balance(coins['vals'][j]))
                chart_data['balances'].append('null') # Javascript null
                j += 1
        # Then add any remaining farmed coins
        while j < len(coins['dates']):
            chart_data['dates'].append(coins['dates'][j])
            chart_data['coins'].append(converters.round_balance(coins['vals'][j]))
            chart_data['balances'].append('null') # Javascript null
            j += 1
        #app.logger.info("{0} -> {1}".format(blockchain, chart_data))
        farm_summary.farms[blockchain]['wallets'] = chart_data
