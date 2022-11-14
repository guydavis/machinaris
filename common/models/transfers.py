import datetime as dt
import sqlalchemy as sa

from sqlalchemy.sql import func

from common.extensions.database import db

class Transfer(db.Model):
    __bind_key__ = 'transfers'
    __tablename__ = "transfers"
    log_file = sa.Column(sa.String, primary_key=True)
    plot_id = sa.Column(sa.String(length=16), nullable=True)
    hostname = sa.Column(sa.String(length=255), nullable=True)
    blockchain = sa.Column(sa.String(length=64), nullable=True)
    k = sa.Column(sa.Integer, nullable=True)
    size = sa.Column(sa.Integer, nullable=True)
    source = sa.Column(sa.String, nullable=True)
    type = sa.Column(sa.String, nullable=True)
    dest = sa.Column(sa.String, nullable=True)
    status = sa.Column(sa.String(length=48), nullable=True)
    rate = sa.Column(sa.String(length=16), nullable=True)
    pct_complete = sa.Column(sa.Integer, nullable=True)
    size_complete = sa.Column(sa.String(length=16), nullable=True)
    start_date = sa.Column(sa.String(length=24), nullable=True)
    end_date = sa.Column(sa.String(length=24), nullable=True)
    duration = sa.Column(sa.String, nullable=True)
    created_at = sa.Column(sa.DateTime(), server_default=func.now())
    updated_at = sa.Column(sa.DateTime(), onupdate=func.now())

    