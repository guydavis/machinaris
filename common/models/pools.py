import datetime as dt
import sqlalchemy as sa

from sqlalchemy.sql import func

from common.extensions.database import db

POOLABLE_BLOCKCHAINS = [ 'chia', 'chives', 'gigahorse' ]

class Pool(db.Model):
    __bind_key__ = 'pools'
    __tablename__ = "pools"

    unique_id = sa.Column(sa.String(length=255), primary_key=True)
    hostname = sa.Column(sa.String(length=255), nullable=False)
    blockchain = sa.Column(sa.String(length=64), nullable=False)
    launcher_id = sa.Column(sa.String(length=255), nullable=False)
    login_link = sa.Column(sa.String, nullable=True)
    pool_state = sa.Column(sa.String, nullable=False)
    updated_at = sa.Column(sa.String(length=64), nullable=False)
    