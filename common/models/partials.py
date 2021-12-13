import datetime as dt
import sqlalchemy as sa

from common.extensions.database import db

class Partial(db.Model):
    __bind_key__ = 'partials'
    __tablename__ = "partials"

    unique_id = sa.Column(sa.String(length=255), primary_key=True)
    hostname = sa.Column(sa.String(length=255), nullable=False)
    blockchain = sa.Column(sa.String(length=64), nullable=False)
    launcher_id = sa.Column(sa.String(length=255), nullable=False)
    pool_url = sa.Column(sa.String(length=255), nullable=False)
    pool_response = sa.Column(sa.String, nullable=False)
    created_at = sa.Column(sa.String(length=64), nullable=False)
    