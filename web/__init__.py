import logging
import os
import pytz
import re

from flask import Flask, request
from flask_babel import Babel
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.engine import Engine
from sqlalchemy import event

from web.default_settings import DefaultConfig

from common.config import globals

app = Flask(__name__)
app.secret_key = b'$}#P)eu0A.O,s0Mz'
app.config.from_object(DefaultConfig)
# Override config with optional settings file
app.config.from_envvar('WEB_SETTINGS_FILE', silent=True)
babel = Babel(app)

@babel.localeselector
def get_locale():
    try:
        accept = request.headers['Accept-Language']
        match = request.accept_languages.best_match(app.config['LANGUAGES'])
        # Workaround for dumb babel match method suggesting 'en' for 'nl' instead of 'nl_NL'
        if match == 'en' and not accept.startswith('en'):
            first_accept = accept.split(',')[0]  # Like 'nl'
            alternative = "{0}_{1}".format(first_accept, first_accept.upper())
            if alternative in app.config['LANGUAGES']:
                return alternative
        app.logger.debug("INIT: Accept-Language: {0}  ---->  matched locale: {1}".format(accept, match))
    except:
        app.logger.debug("INIT: Request had no Accept-Language, returning default locale of en.")
    return request.accept_languages.best_match(app.config['LANGUAGES'])

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
    if value:
        #app.logger.info("{0} => {1}".format(value, value.strftime(format)))
        return value.strftime(format)
    else:
        return ""

app.jinja_env.filters['datetimefilter'] = datetimefilter

def timesecondstrimmer(value):
    if value:
        #app.logger.info("{0} => {1}".format(value, value.strftime(format)))
        return value[:value.rindex(':')]
    else:
        return ""

app.jinja_env.filters['timesecondstrimmer'] = timesecondstrimmer

def plotnameshortener(value):
    #app.logger.info("Shorten: {0}".format(value))
    match = re.match("plot(?:-mmx)?-k(\d+)-(\d+)-(\d+)-(\d+)-(\d+)-(\d+)-(\w+).plot", value)
    if match:
        return "plot-k{0}-{1}-{2}-{3}-{4}-{5}-{6}...".format( match.group(1), 
            match.group(2), match.group(3), match.group(4), match.group(5), match.group(6),
            match.group(7)[:16])
    return value

app.jinja_env.filters['plotnameshortener'] = plotnameshortener

def launcheridshortener(value):
    #app.logger.info("Shorten: {0}".format(value))
    return value[:12] + '...'

app.jinja_env.filters['launcheridshortener'] = launcheridshortener

def alltheblocks_blockchainlink(blockchain):
   alltheblocks_blockchain = globals.get_alltheblocks_name(blockchain)
   return 'https://alltheblocks.net/{0}'.format(alltheblocks_blockchain)

app.jinja_env.filters['alltheblocks_blockchainlink'] = alltheblocks_blockchainlink

def alltheblocks_blocklink(block, blockchain):
    if blockchain == 'mmx':
        return block # No support at ATB for MMX, so don't link it
    alltheblocks_blockchain = globals.get_alltheblocks_name(blockchain)
    return '<a href="https://alltheblocks.net/{0}/block/0x{1}" class="text-white" target="_blank">{1}</a>'.format(alltheblocks_blockchain, block)

app.jinja_env.filters['alltheblocks_blocklink'] = alltheblocks_blocklink

def escape_single_quotes(value):
    return value.replace("'", "\\'")

app.jinja_env.filters['escape_single_quotes'] = escape_single_quotes