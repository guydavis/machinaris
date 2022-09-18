import datetime as dt
import sqlalchemy as sa

from sqlalchemy.sql import func

from common.extensions.database import db

class Warning(db.Model):
    __bind_key__ = 'warnings'
    __tablename__ = "warnings"

    hostname = db.Column(db.String(), primary_key=True)
    blockchain = db.Column(db.String(length=64), primary_key=True)
    type = db.Column(db.String(), primary_key=True)
    service = db.Column(db.String())
    title = db.Column(db.String())
    content = db.Column(db.String())
    created_at = db.Column(db.String())
    updated_at = sa.Column(sa.DateTime(), onupdate=func.now())
    