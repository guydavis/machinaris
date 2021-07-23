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
    since = (datetime.datetime.now() - datetime.timedelta(hours=24)).strftime("%Y%m%d%H%M%S")
    summary['plot_count'] = plot_count_diff(since)
    summary['plots_size'] = plots_size_diff(since)
    summary['total_chia'] = total_coin_diff(since, 'chia')
    summary['total_flax'] = total_coin_diff(since, 'flax')
    summary['netspace_chia'] = netspace_size_diff(since, 'chia')
    summary['netspace_flax'] = netspace_size_diff(since, 'flax')
    summary['daily_summary_chia'] = daily_notification(since, 'chia')
    summary['daily_summary_flax'] = daily_notification(since, 'flax')
    #app.logger.info(summary)
    return summary

def plot_count_diff(since):
    result = '-'
    try:
        latest = db.session.query(StatPlotCount).order_by(StatPlotCount.created_at.desc()).limit(1).first()
        #app.logger.info(latest.value)
        before = db.session.query(StatPlotCount).filter(StatPlotCount.created_at <= since).order_by(StatPlotCount.created_at.desc()).limit(1).first()
        #app.logger.info(before.value)
        result = "%+0g" % (latest.value - before.value)
    except Exception as ex:
        app.logger.info("Failed to query for day diff of plot_count because {0}".format(str(ex)))
    #app.logger.info("Result is: {0}".format(result))
    return result

def plots_size_diff(since):
    result = '-'
    try:
        latest = db.session.query(StatPlotsSize).order_by(StatPlotsSize.created_at.desc()).limit(1).first()
        #app.logger.info(latest.value)
        before = db.session.query(StatPlotsSize).filter(StatPlotsSize.created_at <= since).order_by(StatPlotsSize.created_at.desc()).limit(1).first()
        #app.logger.info(before.value)
        gibs = (latest.value - before.value)
        fmtted = converters.gib_to_fmt(gibs)
        if fmtted == "0.0 B":
            result = "+0"
        elif not fmtted.startswith('-'):
            result = "+{0}".format(fmtted)
        else:
            result = fmtted
    except Exception as ex:
        app.logger.info("Failed to query for day diff of plots_size because {0}".format(str(ex)))
    #app.logger.info("Result is: {0}".format(result))
    return result

def total_coin_diff(since, blockchain):
    result = '-'
    try:
        latest = db.session.query(StatTotalChia).filter(StatTotalChia.blockchain==blockchain).order_by(StatTotalChia.created_at.desc()).limit(1).first()
        #app.logger.info(latest.value)
        before = db.session.query(StatTotalChia).filter(StatTotalChia.blockchain==blockchain, StatTotalChia.created_at <= since).order_by(StatTotalChia.created_at.desc()).limit(1).first()
        #app.logger.info(before.value)
        result = "%+6g" % (latest.value - before.value)
    except Exception as ex:
        app.logger.info("Failed to query for day diff of total_chia because {0}".format(str(ex)))
    #app.logger.info("Result is: {0}".format(result))
    return result

def netspace_size_diff(since, blockchain):
    result = '-'
    try:
        latest = db.session.query(StatNetspaceSize).filter(StatNetspaceSize.blockchain==blockchain).order_by(StatNetspaceSize.created_at.desc()).limit(1).first()
        #app.logger.info(latest.value)
        before = db.session.query(StatNetspaceSize).filter(StatNetspaceSize.blockchain==blockchain, StatNetspaceSize.created_at <= since).order_by(StatNetspaceSize.created_at.desc()).limit(1).first()
        #app.logger.info(before.value)
        gibs = (latest.value - before.value)
        fmtted = converters.gib_to_fmt(gibs)
        if fmtted == "0.000 B":
            result = "+0"
        elif not fmtted.startswith('-'):
            result = "+{0}".format(fmtted)
        else:
            result = fmtted
    except Exception as ex:
        app.logger.info("Failed to query for day diff of netspace_size because {0}".format(str(ex)))
    #app.logger.info("Result is: {0}".format(result))
    return result

def daily_notification(since, blockchain):
    result = '-'
    try:
        result = db.session.query(Alert).filter(
                Alert.blockchain==blockchain, 
                Alert.created_at >= since,
                Alert.priority == "LOW",
                Alert.service == "DAILY",
                Alert.hostname == "aragorn"
            ).order_by(Alert.created_at.desc()).limit(1).first().message
    except Exception as ex:
        app.logger.info("Failed to query for latest daily summary because {0}".format(str(ex)))
    app.logger.info("Result is: {0}".format(result))
    return result