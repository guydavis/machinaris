import datetime as dt
import sqlalchemy as sa

from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, backref

from common.extensions.database import db

class Plot(db.Model):
    __tablename__ = "plots"

    hostname = sa.Column(sa.String(length=255), primary_key=True)
    plot_id = sa.Column(sa.String(length=16), primary_key=True)
    type = sa.Column(sa.String(length=32), nullable=True)
    dir = sa.Column(sa.String(length=255), nullable=False)
    file = sa.Column(sa.String(length=255), nullable=False)
    size = sa.Column(sa.Integer, nullable=False)
    created_at = sa.Column(sa.String(length=64), nullable=False)
    updated_at = sa.Column(sa.DateTime(), onupdate=func.now())
