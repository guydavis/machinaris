import marshmallow as ma
from marshmallow_sqlalchemy import field_for
from marshmallow_toplevel import TopLevelSchema

from api.extensions.api import Schema, AutoSchema
from common.models.stats import StatTimeToWin

class StatTimeToWinSchema(AutoSchema):
    id = field_for(StatTimeToWin, "id")

    class Meta(AutoSchema.Meta):
        table = StatTimeToWin.__table__


class StatTimeToWinQueryArgsSchema(Schema):
    id = ma.fields.Str()
    hostname = ma.fields.Str()

class BatchOfStatTimeToWinSchema(TopLevelSchema):
    _toplevel = ma.fields.Nested(
        StatTimeToWinSchema,
        required=True,
        many=True
    )

class BatchOfStatTimeToWinQueryArgsSchema(Schema):
    hostname = ma.fields.Str()
