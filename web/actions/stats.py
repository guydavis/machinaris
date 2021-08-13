#
# Access to statistics and calculated values.
#

import datetime

from common.utils import converters
from common.models.alerts import Alert
from common.models.stats import StatPlotCount, StatPlotsSize, StatTotalChia, StatNetspaceSize, StatTimeToWin, \
        StatPlotsTotalUsed, StatPlotsDiskUsed, StatPlotsDiskFree, StatPlottingTotalUsed, \
        StatPlottingDiskUsed, StatPlottingDiskFree
from web import app, db, utils

def load_daily_diff():
    summary = {}
    # initialize defaults
    since_date = datetime.datetime.now() - datetime.timedelta(hours=24)
    since_str = since_date.strftime("%Y%m%d%H%M%S")
    summary['plot_count'] = plot_count_diff(since_str)
    summary['plots_size'] = plots_size_diff(since_str)
    summary['total_chia'] = total_coin_diff(since_str, 'chia')
    summary['total_flax'] = total_coin_diff(since_str, 'flax')
    summary['netspace_chia'] = netspace_size_diff(since_str, 'chia')
    summary['netspace_flax'] = netspace_size_diff(since_str, 'flax')
    return summary

def plot_count_diff(since):
    result = ''
    try:
        latest = db.session.query(StatPlotCount).order_by(StatPlotCount.created_at.desc()).limit(1).first()
        #app.logger.info(latest.value)
        before = db.session.query(StatPlotCount).filter(StatPlotCount.created_at <= since).order_by(StatPlotCount.created_at.desc()).limit(1).first()
        #app.logger.info(before.value)
        if (latest.value - before.value) != 0:
            result = "%+0g in last day." % (latest.value - before.value)
    except Exception as ex:
        app.logger.info("Failed to query for day diff of plot_count because {0}".format(str(ex)))
    #app.logger.info("Result is: {0}".format(result))
    return result

def plots_size_diff(since):
    result = ''
    try:
        latest = db.session.query(StatPlotsSize).order_by(StatPlotsSize.created_at.desc()).limit(1).first()
        #app.logger.info(latest.value)
        before = db.session.query(StatPlotsSize).filter(StatPlotsSize.created_at <= since).order_by(StatPlotsSize.created_at.desc()).limit(1).first()
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
        app.logger.info("Failed to query for day diff of plots_size because {0}".format(str(ex)))
    #app.logger.info("Result is: {0}".format(result))
    return result

def total_coin_diff(since, blockchain):
    result = ''
    try:
        latest = db.session.query(StatTotalChia).filter(StatTotalChia.blockchain==blockchain).order_by(StatTotalChia.created_at.desc()).limit(1).first()
        #app.logger.info(latest.value)
        before = db.session.query(StatTotalChia).filter(StatTotalChia.blockchain==blockchain, StatTotalChia.created_at <= since).order_by(StatTotalChia.created_at.desc()).limit(1).first()
        #app.logger.info(before.value)
        if (latest.value - before.value) != 0:
            result = "%+6g in last day." % (latest.value - before.value)
    except Exception as ex:
        app.logger.info("Failed to query for day diff of total_chia because {0}".format(str(ex)))
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
        app.logger.info("Failed to query for day diff of netspace_size because {0}".format(str(ex)))
    #app.logger.info("Result is: {0}".format(result))
    return result

def load_daily_notifications():
    summary = {}
    # initialize defaults
    since_date = datetime.datetime.now() - datetime.timedelta(hours=24)
    summary['daily_summary_chia'] = daily_notifications(since_date, 'chia')
    summary['daily_summary_flax'] = daily_notifications(since_date, 'flax')
    #app.logger.info(summary)
    return summary

def daily_notifications(since, blockchain):
    result = []
    try:
        #app.logger.info(since)
        dailys = db.session.query(Alert).filter(
                Alert.blockchain==blockchain, 
                Alert.created_at >= since,
                Alert.priority == "LOW",
                Alert.service == "DAILY"
            ).order_by(Alert.created_at.desc()).all()
        for daily in dailys:
            #app.logger.info("{0} at {1}".format(daily.hostname, daily.created_at))
            result.append(daily)
    except Exception as ex:
        app.logger.info("Failed to query for latest daily summary because {0}".format(str(ex)))
    result.sort(key=lambda daily: daily.hostname, reverse=False)
    return result