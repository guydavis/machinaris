import datetime as dt
import json as j
import sqlalchemy as sa

from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, backref

from common.extensions.database import db

class Worker(db.Model):
    __tablename__ = "workers"

    hostname = sa.Column(sa.String(length=255), primary_key=True)
    port = sa.Column(sa.Integer, nullable=True)
    blockchain = sa.Column(sa.String(length=255), primary_key=True)
    displayname = sa.Column(sa.String(length=255), nullable=True)
    mode = sa.Column(sa.String(length=64), nullable=False)
    services = sa.Column(sa.String, nullable=False)
    url = sa.Column(sa.String, nullable=False)
    config = sa.Column(sa.String, nullable=False)
    latest_ping_result = sa.Column(sa.String) # Holds status of most recent ping
    ping_success_at = sa.Column(sa.DateTime()) # Time of last successful ping
    created_at = sa.Column(sa.DateTime(), server_default=func.now())
    updated_at = sa.Column(sa.DateTime())

    def farming_status(self):
        try:
            return j.loads(self.services)['farming_status']
        except: # Old key
            return j.loads(self.services)['farm_status']
    
    def plotting_status(self):
        try:
            return j.loads(self.services)['plotting_status']
        except: # Old key
            return j.loads(self.services)['plotman_status']

    def archiving_status(self):
        try:
            return j.loads(self.services)['archiving_status']
        except: # Old key
            return j.loads(self.services)['archiver_status'] 

    def archiving_enabled(self):
        return j.loads(self.config)['archiving_enabled'] 
    
    def monitoring_status(self):
        try:
            return j.loads(self.services)['monitoring_status']
        except: # Old key
            return j.loads(self.services)['chiadog_status'] 
