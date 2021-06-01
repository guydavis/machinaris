# 
# Machinaris API Server  
# - original template from https://github.com/lafrech/flask-smorest-sqlalchemy-example
#

import logging

from flask import Flask

app = Flask('Machinaris API')

if __name__ != '__main__':
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

from api import extensions, views
from api.default_settings import DefaultConfig

app.config.from_object(DefaultConfig)
# Override config with optional settings file
app.config.from_envvar('FLASK_SETTINGS_FILE', silent=True)

api = extensions.create_api(app)
views.register_blueprints(api)

