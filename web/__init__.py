import logging
import os
import pytz
import re

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.engine import Engine
from sqlalchemy import event

from web.default_settings import DefaultConfig

app = Flask(__name__)
app.secret_key = b'$}#P)eu0A.O,s0Mz'
app.config.from_object(DefaultConfig)
# Override config with optional settings file
app.config.from_envvar('WEB_SETTINGS_FILE', silent=True)

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.close()

db = SQLAlchemy(app)

if __name__ != '__main__':
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

app.logger.debug("CONTROLLER_HOST={0}".format(app.config['CONTROLLER_HOST']))

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
    if value: 
        value = utc.localize(value, is_dst=None).astimezone(pytz.utc)
        local_dt = value.astimezone(tz)
        return local_dt.strftime(format)
    else:
        return ""

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