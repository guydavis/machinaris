import os

class DefaultConfig:
    API_TITLE = "Machinaris API"
    API_VERSION = 0.1
    OPENAPI_VERSION = '3.0.2'
    OPENAPI_URL_PREFIX = '/'
    OPENAPI_JSON_PATH = "api-spec.json"
    OPENAPI_REDOC_PATH = '/'
    OPENAPI_REDOC_URL = (
        "https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:////root/.chia/machinaris/dbs/machinaris.db'
    SQLALCHEMY_BINDS = {
        'stats':      'sqlite:////root/.chia/machinaris/dbs/stats.db',
        'chiadog':    'sqlite:////root/.chia/chiadog/dbs/chiadog.db',
    }
    SQLALCHEMY_ECHO = True if 'FLASK_ENV' in os.environ and os.environ['FLASK_ENV'] == "development" else False
    ETAG_DISABLED = True # https://flask-smorest.readthedocs.io/en/latest/etag.html
    CONTROLLER_SCHEME = 'http'
    CONTROLLER_HOST = os.environ['controller_host'] if 'controller_host' in os.environ else 'localhost'
    CONTROLLER_PORT = os.environ['controller_api_port'] if 'controller_api_port' in os.environ else '8927'
