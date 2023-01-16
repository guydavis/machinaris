# 
# Machinaris API Server  
# - original template from https://github.com/lafrech/flask-smorest-sqlalchemy-example
#

import logging

from flask import Flask, request
from flask_babel import Babel
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
babel = Babel(app)

def get_locale():
    #for d in babel.translation_directories:
    #    app.logger.info(d)
    #app.logger.info("API=> Returning locale: {0}".format(request.accept_languages.best_match(app.config['LANGUAGES'])))
    return request.accept_languages.best_match(app.config['LANGUAGES'])

from common.extensions.database import db
migrate = Migrate(app, db)

api = extensions.create_api(app)
views.register_blueprints(api)
