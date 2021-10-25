import marshmallow as ma
from marshmallow_sqlalchemy import field_for
from marshmallow_toplevel import TopLevelSchema

from api.extensions.api import Schema, AutoSchema
from common.models.stats import StatPlotsSize

class StatPlotsSizeSchema(AutoSchema):
    id = field_for(StatPlotsSize, "id")

    class Meta(AutoSchema.Meta):
        table = StatPlotsSize.__table__


class StatPlotsSizeQueryArgsSchema(Schema):
    id = ma.fields.Str()
    hostname = ma.fields.Str()

class BatchOfStatPlotsSizeSchema(TopLevelSchema):
    _toplevel = ma.fields.Nested(
        StatPlotsSizeSchema,
        required=True,
        many=True
    )

class BatchOfStatPlotsSizeQueryArgsSchema(Schema):
    hostname = ma.fields.Str()
