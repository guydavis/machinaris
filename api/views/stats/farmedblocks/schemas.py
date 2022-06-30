import marshmallow as ma
from marshmallow_sqlalchemy import field_for
from marshmallow_toplevel import TopLevelSchema

from api.extensions.api import Schema, AutoSchema
from common.models.stats import StatFarmedBlocks

class StatFarmedBlocksSchema(AutoSchema):
    id = field_for(StatFarmedBlocks, "id")

    class Meta(AutoSchema.Meta):
        table = StatFarmedBlocks.__table__


class StatFarmedBlocksQueryArgsSchema(Schema):
    id = ma.fields.Str()
    hostname = ma.fields.Str()

class BatchOfStatFarmedBlocksSchema(TopLevelSchema):
    _toplevel = ma.fields.Nested(
        StatFarmedBlocksSchema,
        required=True,
        many=True
    )

class BatchOfStatFarmedBlocksQueryArgsSchema(Schema):
    hostname = ma.fields.Str()
