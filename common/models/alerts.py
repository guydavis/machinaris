import datetime as dt
import sqlalchemy as sa

from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, backref

from common.extensions.database import db

class Alert(db.Model):
    __tablename__ = "alerts"

    unique_id = sa.Column(sa.String(length=128), primary_key=True)
    hostname = sa.Column(sa.String(length=255), nullable=False)
    priority = sa.Column(sa.String(64), nullable=False)
    service = sa.Column(sa.String(64), nullable=False)
    message = sa.Column(sa.String, nullable=False)
    created_at = sa.Column(sa.DateTime(), server_default=func.now())
    updated_at = sa.Column(sa.DateTime(), onupdate=func.now())
