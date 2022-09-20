#
# Performs an hourly insert of latest stats for the farm summary
#

import datetime
import sqlite3
import traceback

from flask import g

from common.config import globals
from common.models import stats
from common.utils import converters
from api import app, utils, db
from api.commands import chia_cli, mmx_cli

DELETE_OLD_STATS_AFTER_DAYS = 90

TABLES = [ stats.StatPlotCount, stats.StatPlotsSize, stats.StatNetspaceSize, stats.StatTimeToWin, stats.StatTotalCoins, ]

def delete_old_stats():
    try:
        cutoff = datetime.datetime.now() - datetime.timedelta(days=DELETE_OLD_STATS_AFTER_DAYS)
        for table in TABLES:
            db.session.query(table).filter(table.created_at <= cutoff.strftime("%Y%m%d%H%M")).delete()
        db.session.commit()
    except:
        app.logger.info("Failed to delete old statistics.")
        app.logger.info(traceback.format_exc())

def collect():
    with app.app_context():
        gc = globals.load()
        delete_old_stats()
        if not gc['farming_enabled']:
            app.logger.info(
                "Skipping farm summary stats collection as not farming on this Machinaris instance.")
            return
        #app.logger.info("Collecting stats about the farm.")
        current_datetime = datetime.datetime.now().strftime("%Y%m%d%H%M")
        for blockchain in globals.enabled_blockchains():
            if blockchain == 'mmx':
                farm_summary = mmx_cli.load_farm_info(blockchain)
            else:
                farm_summary = chia_cli.load_farm_summary(blockchain)
            if not gc['is_controller']:
                store_locally(blockchain, farm_summary, current_datetime)
            send_to_controller(blockchain, farm_summary, current_datetime)

def store_locally(blockchain, farm_summary, current_datetime):
    hostname = utils.get_hostname()
    try:
        db.session.add(stats.StatPlotCount(hostname=hostname, blockchain=blockchain, value=farm_summary.plot_count, created_at=current_datetime))
    except:
        app.logger.info(traceback.format_exc())
    try:
        db.session.add(stats.StatPlotsSize(hostname=hostname, blockchain=blockchain, value=converters.str_to_gibs(farm_summary.plots_size), created_at=current_datetime))
    except:
        app.logger.info(traceback.format_exc())
    if farm_summary.status == "Farming":  # Only collect if fully synced
        try:
            db.session.add(stats.StatTotalCoins(hostname=hostname, blockchain=blockchain, value=farm_summary.total_coins, created_at=current_datetime))
        except:
            app.logger.info(traceback.format_exc())
        try:
            db.session.add(stats.StatNetspaceSize(hostname=hostname, blockchain=blockchain, value=converters.str_to_gibs(farm_summary.netspace_size), created_at=current_datetime))
        except:
            app.logger.info(traceback.format_exc())
        try:
            db.session.add(stats.StatTimeToWin(hostname=hostname, blockchain=blockchain, value=converters.etw_to_minutes(farm_summary.time_to_win), created_at=current_datetime))
        except:
            app.logger.info(traceback.format_exc())
    db.session.commit()

def send_to_controller(blockchain, farm_summary, current_datetime):
       send_stat(blockchain, '/stats/plotcount/', farm_summary.plot_count,current_datetime)
       send_stat(blockchain, '/stats/plotssize/', converters.str_to_gibs(farm_summary.plots_size),current_datetime)
       if farm_summary.status == "Farming":  # Only collect if fully synced
            send_stat(blockchain, '/stats/totalcoins/', farm_summary.total_coins, current_datetime)
            send_stat(blockchain, '/stats/netspacesize/', converters.str_to_gibs(farm_summary.netspace_size) ,current_datetime)
            send_stat(blockchain, '/stats/timetowin/', converters.etw_to_minutes(farm_summary.time_to_win), current_datetime)

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
