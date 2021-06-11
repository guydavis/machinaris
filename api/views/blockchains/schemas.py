import marshmallow as ma
from marshmallow_sqlalchemy import field_for

from api.extensions.api import Schema, AutoSchema
from common.models.blockchains import Blockchain


class BlockchainSchema(AutoSchema):
    hostname = field_for(Blockchain, "hostname")

    class Meta(AutoSchema.Meta):
        table = Blockchain.__table__


class BlockchainQueryArgsSchema(Schema):
    hostname = ma.fields.Str()
