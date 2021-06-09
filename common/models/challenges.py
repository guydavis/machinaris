import datetime as dt
import sqlalchemy as sa

from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, backref

from common.extensions.database import db

class Challenge(db.Model):
    __tablename__ = "challenges"

    unique_id = sa.Column(sa.String(length=64), primary_key=True)
    hostname = sa.Column(sa.String(length=255), nullable=False)
    challenge_id = sa.Column(sa.String(length=64), nullable=False)
    plots_past_filter = sa.Column(sa.String(length=32), nullable=False)
    proofs_found = sa.Column(sa.Integer, nullable=False)
    time_taken = sa.Column(sa.String(length=32), nullable=False)
    created_at = sa.Column(sa.String(length=64), nullable=False)
    