import datetime as dt
import sqlalchemy as sa

from sqlalchemy.sql import func

from common.extensions.database import db

class Plotnft(db.Model):
    __bind_key__ = 'plotnfts'
    __tablename__ = "plotnfts"

    unique_id = sa.Column(sa.String(length=255), primary_key=True)
    hostname = sa.Column(sa.String(length=255), nullable=False)
    blockchain = sa.Column(sa.String(length=64), nullable=False)
    launcher = sa.Column(sa.String, nullable=False)
    wallet_num = sa.Column(sa.Integer, nullable=False)
    header = sa.Column(sa.String, nullable=False)
    details = sa.Column(sa.String, nullable=False)
    created_at = sa.Column(sa.DateTime(), server_default=func.now())
    updated_at = sa.Column(sa.DateTime(), onupdate=func.now())

    def pool_contract_address(self):
        for line in self.details.split('\n'):
            if line.startswith("Pool contract address"):
                return line.split(':')[1].strip()
        return None

    def current_pool_url(self):
        for line in self.details.split('\n'):
            if "Current pool URL:" in line:
                return line[len("Current pool URL:"):].strip()
            elif "Target state: SELF_POOLING" in line:
                return None  # Switching back to self-pooling, no pool_url
        return None