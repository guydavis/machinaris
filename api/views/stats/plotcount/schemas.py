import marshmallow as ma
from marshmallow_sqlalchemy import field_for
from marshmallow_toplevel import TopLevelSchema

from api.extensions.api import Schema, AutoSchema
from common.models.stats import StatPlotCount

class StatPlotCountSchema(AutoSchema):
    id = field_for(StatPlotCount, "id")

    class Meta(AutoSchema.Meta):
        table = StatPlotCount.__table__


class StatPlotCountQueryArgsSchema(Schema):
    id = ma.fields.Str()
    hostname = ma.fields.Str()

class BatchOfStatPlotCountSchema(TopLevelSchema):
    _toplevel = ma.fields.Nested(
        StatPlotCountSchema,
        required=True,
        many=True
    )

class BatchOfStatPlotCountQueryArgsSchema(Schema):
    hostname = ma.fields.Str()
