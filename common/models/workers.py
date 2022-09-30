import datetime as dt
import json as j
import sqlalchemy as sa

from sqlalchemy.sql import func

from common.extensions.database import db

class Worker(db.Model):
    __bind_key__ = 'workers'
    __tablename__ = "workers"

    hostname = sa.Column(sa.String(length=255), primary_key=True)
    port = sa.Column(sa.Integer, primary_key=True)
    blockchain = sa.Column(sa.String(length=64), nullable=False)
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
            try:
                return j.loads(self.services)['farm_status']
            except:
                return "unknown"
    
    def plotting_status(self):
        try:
            return j.loads(self.services)['plotting_status']
        except: # Old key
            try:
                return j.loads(self.services)['plotman_status']
            except:
                return "unknown"

    def archiving_status(self):
        try:
            return j.loads(self.services)['archiving_status']
        except: # Old key
            try:
                return j.loads(self.services)['archiver_status']
            except:
                return "unknown"

    def archiving_enabled(self):
        try:
            return j.loads(self.config)['archiving_enabled']
        except:
            return "unknown"
    
    def monitoring_status(self):
        try:
            return j.loads(self.services)['monitoring_status']
        except: # Old key
            try:
                return j.loads(self.services)['chiadog_status'] 
            except:
                return "unknown"
    
    def container_memory_usage_gb(self):
        try:
            return "{:.2f} GB".format(int(j.loads(self.services)['container_memory_usage_bytes']) / 1024 / 1024 / 1024)
        except Exception as ex:
            return ''
    
    def connection_status(self):
        fifteen_mins_ago = dt.datetime.now() - dt.timedelta(minutes=15)
        if self.ping_success_at and self.ping_success_at >= fifteen_mins_ago:
            return self.latest_ping_result
        elif self.latest_ping_result and self.latest_ping_result == 'Responding':
            return "offline" # Was responding but over 15 minutes ago
        return self.latest_ping_result

    def machinaris_version(self):
        try:
            return j.loads(self.config)['machinaris_version']
        except:
            return None

    def fullnode_db_version(self):
        try:
            return j.loads(self.config)['fullnode_db_version']
        except:
            return None
