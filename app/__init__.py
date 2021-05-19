import logging

from flask import Flask

app = Flask(__name__)
app.secret_key = b'$}#P)eu0A.O,s0Mz'

if __name__ != '__main__':
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

from app import routes
