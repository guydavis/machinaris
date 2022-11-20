import datetime as dt
import sqlalchemy as sa

from sqlalchemy.sql import func

from common.extensions.database import db

# Currently supported ksizes for replot free space
KSIZES = [29, 30, 31, 32, 33, 34] 

class Plot(db.Model):
    __bind_key__ = 'plots'
    __tablename__ = "plots"

    hostname = sa.Column(sa.String(length=255), primary_key=True)
    displayname = sa.Column(sa.String(length=255), nullable=True)
    blockchain = sa.Column(sa.String(length=64), nullable=False)
    plot_id = sa.Column(sa.String(length=16), primary_key=True)
    type = sa.Column(sa.String(length=32), nullable=False)
    dir = sa.Column(sa.String(length=255), nullable=False)
    file = sa.Column(sa.String(length=255), nullable=False)
    size = sa.Column(sa.Integer, nullable=False)
    plot_check = sa.Column(sa.String(length=255), nullable=True)
    plot_analyze = sa.Column(sa.String(length=255), nullable=True)
    created_at = sa.Column(sa.String(length=64), nullable=False)
    updated_at = sa.Column(sa.DateTime(), onupdate=func.now())
