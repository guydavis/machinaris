import datetime as dt
import sqlalchemy as sa

from sqlalchemy.sql import func

from common.extensions.database import db

class Plotting(db.Model):
    __bind_key__ = 'plottings'
    __tablename__ = "plottings"

    plot_id = sa.Column(sa.String(length=8), primary_key=True)
    hostname = sa.Column(sa.String(length=255), nullable=False)
    plotter = sa.Column(sa.String(length=64), nullable=False)
    blockchain = sa.Column(sa.String(length=64), nullable=False)
    k = sa.Column(sa.Integer, nullable=False)
    tmp = sa.Column(sa.String(length=255), nullable=False)
    dst = sa.Column(sa.String(length=255), nullable=False)
    wall = sa.Column(sa.String(length=8), nullable=False)
    phase = sa.Column(sa.String(length=8), nullable=False)
    size = sa.Column(sa.String(length=8), nullable=False)
    pid = sa.Column(sa.Integer, nullable=False)
    stat = sa.Column(sa.String(length=8), nullable=False)
    mem = sa.Column(sa.String(length=8), nullable=False)
    user = sa.Column(sa.String(length=8), nullable=False)
    sys = sa.Column(sa.String(length=8), nullable=False)
    io = sa.Column(sa.String(length=8), nullable=False)
    created_at = sa.Column(sa.DateTime(), server_default=func.now())
    updated_at = sa.Column(sa.DateTime(), onupdate=func.now())

    