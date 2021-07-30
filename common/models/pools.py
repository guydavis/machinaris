import datetime as dt
import sqlalchemy as sa

from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, backref

from common.extensions.database import db

class Pool(db.Model):
    __tablename__ = "pools"

    unique_id = sa.Column(sa.String(length=255), primary_key=True)
    hostname = sa.Column(sa.String(length=255), nullable=False)
    blockchain = sa.Column(sa.String(length=64), nullable=True)
    launcher_id = sa.Column(sa.String(length=255), nullable=False)
    pool_state = sa.Column(sa.String, nullable=False)
    updated_at = sa.Column(sa.String(length=64), nullable=False)
    