#
# Common utility methods
#

import logging
import re
import traceback

def sizeof_fmt(num, suffix='B'):
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return "%3.3f %s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.3f %s%s" % (num, 'Yi', suffix)

def gib_to_fmt(gibs):
    return sizeof_fmt(gibs * 1024 * 1024 * 1024)

def str_to_gibs(str):
    try:
        val,unit = str.split(' ')
        if unit.lower().strip().endswith('gib'):
            return float(val)
        elif unit.lower().strip().endswith('tib'):
            return float(val) * 1024
        elif unit.lower().strip().endswith('pib'):
            return float(val) * 1024 * 1024
        elif unit.lower().strip().endswith('eib'):
            return float(val) * 1024 * 1024 * 1024
    except:
        logging.info("Failed to convert to GiB: {0}".format(str))
        logging.info(traceback.format_exc())
        return None

# Convert expected time to win back to minutes.  See https://github.com/Chia-Network/chia-blockchain/blob/9e21716965f6f6250f6fe4b3449a66f20794d3d9/chia/util/misc.py#L18
def etw_to_minutes(etw):
    logging.info("ETW='{0}'".format(etw))
    etw_total_minutes = 0
    hour_minutes = 60
    day_minutes = 24 * hour_minutes
    week_minutes = 7 * day_minutes
    months_minutes = 43800
    year_minutes = 12 * months_minutes
    match = re.search("(\d+) year", etw)
    if match:
        etw_total_minutes += int(match.group(1)) * year_minutes
    match = re.search("(\d+) month", etw)
    if match:
        etw_total_minutes += int(match.group(1)) * months_minutes
    match = re.search("(\d+) week", etw)
    if match:
        etw_total_minutes += int(match.group(1)) * week_minutes
    match = re.search("(\d+) day", etw)
    if match:
        etw_total_minutes += int(match.group(1)) * day_minutes
    match = re.search("(\d+) hour", etw)
    if match:
        etw_total_minutes += int(match.group(1)) * hour_minutes
    match = re.search("(\d+) minute", etw)
    if match:
        etw_total_minutes += int(match.group(1), etw)
    return etw_total_minutes