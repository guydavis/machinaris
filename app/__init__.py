import logging

from flask import Flask

app = Flask(__name__)
app.secret_key = b'$}#P)eu0A.O,s0Mz'

if __name__ != '__main__':
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

from app import routes


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
