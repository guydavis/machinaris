import datetime as dt
import sqlalchemy as sa

from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, backref

from common.extensions.database import db

class Plotting(db.Model):
    __tablename__ = "plottings"

    plot_id = sa.Column(sa.String(length=8), primary_key=True)
    hostname = sa.Column(sa.String(length=255))
    k = sa.Column(sa.Integer)
    tmp = sa.Column(sa.String(length=255))
    dst = sa.Column(sa.String(length=255))
    wall = sa.Column(sa.String(length=8))
    phase = sa.Column(sa.String(length=8))
    size = sa.Column(sa.String(length=8))
    pid = sa.Column(sa.Integer)
    stat = sa.Column(sa.String(length=8))
    mem = sa.Column(sa.String(length=8))
    user = sa.Column(sa.String(length=8))
    sys = sa.Column(sa.String(length=8))
    io = sa.Column(sa.String(length=8))
    created_at = sa.Column(sa.DateTime(), server_default=func.now())
    updated_at = sa.Column(sa.DateTime(), onupdate=func.now())

    