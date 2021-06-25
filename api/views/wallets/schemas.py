import marshmallow as ma
from marshmallow_sqlalchemy import field_for

from api.extensions.api import Schema, AutoSchema
from common.models.wallets import Wallet


class WalletSchema(AutoSchema):
    hostname = field_for(Wallet, "hostname")

    class Meta(AutoSchema.Meta):
        table = Wallet.__table__


class WalletQueryArgsSchema(Schema):
    hostname = ma.fields.Str()
