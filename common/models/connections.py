import datetime as dt
import sqlalchemy as sa

from sqlalchemy.sql import func

from common.extensions.database import db

class Connection(db.Model):
    __bind_key__ = 'connections'
    __tablename__ = "connections"

    hostname = sa.Column(sa.String(length=255), primary_key=True)
    blockchain = sa.Column(sa.String(length=64), primary_key=True)
    details = sa.Column(sa.String, nullable=False)
    created_at = sa.Column(sa.DateTime(), server_default=func.now())
    updated_at = sa.Column(sa.DateTime(), onupdate=func.now())
