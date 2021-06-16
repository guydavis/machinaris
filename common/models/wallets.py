import datetime as dt
import sqlalchemy as sa

from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, backref

from common.extensions.database import db

class Wallet(db.Model):
    __tablename__ = "wallets"

    hostname = sa.Column(sa.String(length=255), primary_key=True)
    details = sa.Column(sa.String, nullable=False)
    created_at = sa.Column(sa.DateTime(), server_default=func.now())
    updated_at = sa.Column(sa.DateTime(), onupdate=func.now())
