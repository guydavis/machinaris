#
# Common utility methods
#

import math
import re
import traceback

def sizeof_fmt(num, suffix='B'):
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return "%3.3f %s%s" % (num, unit, suffix)
        num /= 1024.0
    value = "%.3f %s%s" % (num, 'Yi', suffix)
    if value == "0.000 B":
        return "0"
    return value

def convert_size(size_bytes):
   if size_bytes == 0:
       return "0B"
   size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
   i = int(math.floor(math.log(size_bytes, 1024)))
   p = math.pow(1024, i)
   s = round(size_bytes / p, 2)
   return "%s %s" % (s, size_name[i])

def gib_to_fmt(gibs):
    return sizeof_fmt(gibs * 1024 * 1024 * 1024)

def str_to_gibs(str):
    if str == "Unknown":
        return 0.0
    try:
        val,unit = str.split(' ')
        if unit.lower().strip().endswith('mib'):
            return float(val) / 1024
        elif unit.lower().strip().endswith('gib'):
            return float(val)
        elif unit.lower().strip().endswith('tib'):
            return float(val) * 1024
        elif unit.lower().strip().endswith('pib'):
            return float(val) * 1024 * 1024
        elif unit.lower().strip().endswith('eib'):
            return float(val) * 1024 * 1024 * 1024
    except:
        print("Failed to convert to GiB: {0}".format(str))
        print(traceback.format_exc())
        return 0.0

def convert_date_for_luxon(datestr):
    year = datestr[:4]
    month = datestr[4:6]
    day = datestr[6:8]
    time = datestr[8:]
    return "{0}-{1}-{2}T{3}".format(year, month, day, time)

def round_balance(value):
    if abs(value) < 10 and abs(value) >= 1:
        return "%.1f"% round(value, 2)
    elif value > 1:
        return f"{value:n}"
    return str(round(value, 4))

##################################################################################################
#
# Chia™-blockchain - Apache Software License code below.
# For full license see: https://github.com/Chia-Network/chia-blockchain/blob/main/LICENSE
# 
# Convert expected time to win back to minutes.  
# See https://github.com/Chia-Network/chia-blockchain/blob/9e21716965f6f6250f6fe4b3449a66f20794d3d9/chia/util/misc.py#L18
def etw_to_minutes(etw):
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

# Convert an expected time to win in minutes into human-readable units.
# https://github.com/Chia-Network/chia-blockchain/blob/9e21716965f6f6250f6fe4b3449a66f20794d3d9/chia/util/misc.py#L18
def format_minutes(minutes: int) -> str:
    if not isinstance(minutes, int):
        return "Invalid"
    if minutes == 0:
        return "Now"
    hour_minutes = 60
    day_minutes = 24 * hour_minutes
    week_minutes = 7 * day_minutes
    months_minutes = 43800
    year_minutes = 12 * months_minutes
    years = int(minutes / year_minutes)
    months = int(minutes / months_minutes)
    weeks = int(minutes / week_minutes)
    days = int(minutes / day_minutes)
    hours = int(minutes / hour_minutes)
    def format_unit_string(str_unit: str, count: int) -> str:
        return f"{count} {str_unit}{('s' if count > 1 else '')}"
    def format_unit(unit: str, count: int, unit_minutes: int, next_unit: str, next_unit_minutes: int) -> str:
        formatted = format_unit_string(unit, count)
        minutes_left = minutes % unit_minutes
        if minutes_left >= next_unit_minutes:
            formatted += " and " + format_unit_string(next_unit, int(minutes_left / next_unit_minutes))
        return formatted
    if years > 0:
        return format_unit("year", years, year_minutes, "month", months_minutes)
    if months > 0:
        return format_unit("month", months, months_minutes, "week", week_minutes)
    if weeks > 0:
        return format_unit("week", weeks, week_minutes, "day", day_minutes)
    if days > 0:
        return format_unit("day", days, day_minutes, "hour", hour_minutes)
    if hours > 0:
        return format_unit("hour", hours, hour_minutes, "minute", 1)
    if minutes > 0:
        return format_unit_string("minute", minutes)
    return "Unknown"
