import os

class DefaultConfig:
    API_TITLE = "Machinaris WEB"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:////root/.chia/machinaris/dbs/machinaris.db'
    SQLALCHEMY_ECHO = True
    CONTROLLER_SCHEME = 'http'
    CONTROLLER_HOST = os.environ['controller_host']
    CONTROLLER_PORT = os.environ['controller_api_port'] if 'controller_api_port' in os.environ else '8926'
