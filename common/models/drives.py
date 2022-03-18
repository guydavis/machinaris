import datetime as dt
import sqlalchemy as sa

from sqlalchemy.sql import func

from common.extensions.database import db

class Drive(db.Model):
    __bind_key__ = 'drives'
    __tablename__ = "drives"

    serial_number = sa.Column(sa.String(), primary_key=True)
    hostname = sa.Column(sa.String(length=255), nullable=False)
    blockchain = sa.Column(sa.String(length=64), nullable=False)
    model_family = sa.Column(sa.String(), nullable=True)
    device_model = sa.Column(sa.String(), nullable=True)
    device = sa.Column(sa.String(), nullable=True)
    status = sa.Column(sa.String(), nullable=True)
    type = sa.Column(sa.String(), nullable=True)
    comment = sa.Column(sa.String(), nullable=True)
    temperature = sa.Column(sa.REAL, nullable=True)
    power_on_hours = sa.Column(sa.REAL, nullable=True)
    size_gibs = sa.Column(sa.REAL, nullable=True)
    capacity = sa.Column(sa.String(), nullable=True)
    smart_info = sa.Column(sa.String(), nullable=True)
    created_at = sa.Column(sa.DateTime(), server_default=func.now())
    updated_at = sa.Column(sa.DateTime(), onupdate=func.now())
    