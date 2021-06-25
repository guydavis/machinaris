# 
# Machinaris API Server  
# - original template from https://github.com/lafrech/flask-smorest-sqlalchemy-example
#

import logging

from flask import Flask
from flask_migrate import Migrate
from sqlalchemy.engine import Engine
from sqlalchemy import event

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.close()

app = Flask('Machinaris API')

if __name__ != '__main__':
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

from api import extensions, views
from api.default_settings import DefaultConfig

app.config.from_object(DefaultConfig)
# Override config with optional settings file
app.config.from_envvar('API_SETTINGS_FILE', silent=True)

from common.extensions.database import db
migrate = Migrate(app, db)

api = extensions.create_api(app)
views.register_blueprints(api)

#
# Notes about using flask-migrate to manage schema:
# From then on as developer, modify models, then run this to generate a new migration and commit it.
# cd /code/machinaris/api
# FLASK_APP=__init__.py flask db migrate -> Creates migration based on current model.
#
# Then in scripts/setup_databases.sh, this is run on each launch
# cd /machinaris/api
# FLASK_APP=__init__.py flask db upgrade -> Applies migrations against old db
#
#
# Notes about the initial setup:
#
# To create very first migration, point to empty sqlite db, by putting these default_settings.py
#SQLALCHEMY_DATABASE_URI = 'sqlite:///'
#SQLALCHEMY_BINDS = {
#    'stats':      'sqlite:///',
#    'chiadog':    'sqlite:///',
#}
# cd /code/machinaris/api
# FLASK_APP=__init__.py flask db init --multidb
# FLASK_APP=__init__.py flask db migrate
# 