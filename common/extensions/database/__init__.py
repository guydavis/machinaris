import logging
import traceback

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()  

def init_app(app):
    db.init_app(app)
    # No longer necessary here to create tables as flask-migrate manages this
    #try:
    #    db.create_all(app=app)
    #except:
    #    logging.error("Failed to create all for db. {0}".format(traceback.format_exc()))
    #    traceback.print_exc()
