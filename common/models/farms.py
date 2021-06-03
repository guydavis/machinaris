import datetime as dt
import sqlalchemy as sa

from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, backref

from common.extensions.database import db

class Farm(db.Model):
    __tablename__ = "farms"

    hostname = sa.Column(sa.String(length=255), primary_key=True,)
    mode = sa.Column(sa.String(length=12))
    status = sa.Column(sa.String(length=64))
    plot_count = sa.Column(sa.Integer)
    plots_size = sa.Column(sa.REAL)  # GiB
    total_chia = sa.Column(sa.REAL) 
    netspace_size = sa.Column(sa.REAL)  # GiB
    expected_time_to_win = sa.Column(sa.Integer)  # Days
    created_at = sa.Column(sa.DateTime(), server_default=func.now())
    updated_at = sa.Column(sa.DateTime(), onupdate=func.now())

