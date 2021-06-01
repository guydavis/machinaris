import datetime as dt
import sqlalchemy as sa

from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, backref

from api.extensions.database import db


class Alert(db.Model):
    __tablename__ = "alerts"

    id = sa.Column(sa.Integer, primary_key=True)
    priority = sa.Column(sa.String(40), nullable=False)
    service = sa.Column(sa.String(60), nullable=False)
    message = sa.Column(sa.String, nullable=False)
    created_at = sa.Column(sa.DateTime(), server_default=func.now())
    updated_at = sa.Column(sa.DateTime(), onupdate=func.now())
