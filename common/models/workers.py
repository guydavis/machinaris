import datetime as dt
import sqlalchemy as sa

from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, backref

from common.extensions.database import db

class Worker(db.Model):
    __tablename__ = "workers"

    hostname = sa.Column(sa.String(length=255), primary_key=True)
    mode = sa.Column(sa.String(length=40), nullable=False)
    plotting = sa.Column(sa.String(length=40), nullable=False)
    url = sa.Column(sa.String, nullable=False)
    config = sa.Column(sa.String, nullable=False)
    created_at = sa.Column(sa.DateTime(), server_default=func.now())
    updated_at = sa.Column(sa.DateTime(), onupdate=func.now())
