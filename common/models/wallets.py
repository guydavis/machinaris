import datetime as dt
import sqlalchemy as sa

from sqlalchemy.sql import func

from common.extensions.database import db

class Wallet(db.Model):
    __bind_key__ = 'wallets'
    __tablename__ = "wallets"

    hostname = sa.Column(sa.String(length=255), primary_key=True)
    blockchain = sa.Column(sa.String(length=64), primary_key=True)
    details = sa.Column(sa.String, nullable=False)
    cold_balance = sa.Column(sa.String, nullable=True)
    created_at = sa.Column(sa.DateTime(), server_default=func.now())
    updated_at = sa.Column(sa.DateTime(), onupdate=func.now())

    def wallet_id(self):
        for line in self.details.split('\n'):
            if line.startswith("Balances, fingerprint:"):
                return line.split(':')[1].strip()
        return None

    def is_synced(self):
        for line in self.details.split('\n'):
            if line.strip().startswith("Sync status: Synced"):
                return True
        return False

    def has_few_mojos(self):
        for line in self.details.split('\n'):
            if line.strip().startswith("-Spendable") and "(0" in line:
                return True
        return False
