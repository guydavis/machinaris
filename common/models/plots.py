import datetime as dt
import sqlalchemy as sa

from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, backref

from common.extensions.database import db

class Plot(db.Model):
    __tablename__ = "plots"

    plot_id = sa.Column(sa.String(length=8), primary_key=True)
    hostname = sa.Column(sa.String(length=255), nullable=False)
    dir = sa.Column(sa.String(length=255), nullable=False)
    file = sa.Column(sa.String(length=255), nullable=False)
    size = sa.Column(sa.Integer, nullable=False)
    created_at = sa.Column(sa.String(length=64), nullable=False)
    updated_at = sa.Column(sa.DateTime(), onupdate=func.now())

    