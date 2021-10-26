import datetime as dt
import sqlalchemy as sa

from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, backref

from common.extensions.database import db

class Plotnft(db.Model):
    __tablename__ = "plotnfts"

    hostname = sa.Column(sa.String(length=255), primary_key=True)
    blockchain = sa.Column(sa.String(length=64), primary_key=True)
    details = sa.Column(sa.String, nullable=False)
    created_at = sa.Column(sa.DateTime(), server_default=func.now())
    updated_at = sa.Column(sa.DateTime(), onupdate=func.now())

    def launcher_id(self):
        for line in self.details.split('\n'):
            if line.startswith("Launcher ID:"):
                return line.split(':')[1].strip()
        return None

    def pool_contract_address(self):
        for line in self.details.split('\n'):
            if line.startswith("Pool contract address"):
                return line.split(':')[1].strip()
        return None