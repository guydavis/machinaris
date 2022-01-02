import marshmallow as ma
from marshmallow_sqlalchemy import field_for
from marshmallow_toplevel import TopLevelSchema

from api.extensions.api import Schema, AutoSchema
from common.models.stats import StatTotalCoins

class StatTotalCoinsSchema(AutoSchema):
    id = field_for(StatTotalCoins, "id")

    class Meta(AutoSchema.Meta):
        table = StatTotalCoins.__table__


class StatTotalCoinsQueryArgsSchema(Schema):
    id = ma.fields.Str()
    hostname = ma.fields.Str()

class BatchOfStatTotalCoinsSchema(TopLevelSchema):
    _toplevel = ma.fields.Nested(
        StatTotalCoinsSchema,
        required=True,
        many=True
    )

class BatchOfStatTotalCoinsQueryArgsSchema(Schema):
    hostname = ma.fields.Str()
