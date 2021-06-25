import datetime as dt
import sqlalchemy as sa

from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, backref

from common.extensions.database import db

class Farm(db.Model):
    __tablename__ = "farms"

    hostname = sa.Column(sa.String(length=255), primary_key=True,)
    mode = sa.Column(sa.String(length=32), nullable=False)
    status = sa.Column(sa.String(length=128), nullable=False)
    plot_count = sa.Column(sa.Integer, nullable=False)
    plots_size = sa.Column(sa.REAL, nullable=False)  # GiB
    total_chia = sa.Column(sa.REAL, nullable=False) 
    netspace_size = sa.Column(sa.REAL, nullable=False)  # GiB
    expected_time_to_win = sa.Column(sa.String(length=64), nullable=False)
    created_at = sa.Column(sa.DateTime(), server_default=func.now())
    updated_at = sa.Column(sa.DateTime(), onupdate=func.now())

