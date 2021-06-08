import logging
import os
import pytz
import re

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = b'$}#P)eu0A.O,s0Mz'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////root/.chia/machinaris/dbs/machinaris.db'
db = SQLAlchemy(app)

if __name__ != '__main__':
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

from web import routes

# Jinja template filters
@app.template_filter()
def bytesfilter(num, suffix='B'):
    """Convert a number of bytes to a human-readable format."""
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return "%3.0f %s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.0f %s%s" % (num, 'Yi', suffix)

app.jinja_env.filters['bytesfilter'] = bytesfilter

def datetimefilter(value, format="%Y-%m-%d %H:%M"):
    tz = pytz.timezone(os.environ['TZ'])
    utc = pytz.timezone('UTC')  
    value = utc.localize(value, is_dst=None).astimezone(pytz.utc)
    local_dt = value.astimezone(tz)
    return local_dt.strftime(format)

app.jinja_env.filters['datetimefilter'] = datetimefilter

def plotnameshortener(value):
    #app.logger.info("Shorten: {0}".format(value))
    match = re.match("plot-k(\d+)-(\d+)-(\d+)-(\d+)-(\d+)-(\d+)-(\w+).plot", value)
    if match:
        return "plot-k{0}-{1}-{2}-{3}-{4}-{5}-{6}...".format( match.group(1), 
            match.group(2), match.group(3), match.group(4), match.group(5), match.group(5),
            match.group(7)[:20])
    return value

app.jinja_env.filters['plotnameshortener'] = plotnameshortener