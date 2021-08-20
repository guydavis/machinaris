import marshmallow as ma
from marshmallow_sqlalchemy import field_for
from marshmallow_toplevel import TopLevelSchema

from api.extensions.api import Schema, AutoSchema
from common.models.stats import StatPlotsDiskFree

class StatPlotsDiskFreeSchema(AutoSchema):
    id = field_for(StatPlotsDiskFree, "id")

    class Meta(AutoSchema.Meta):
        table = StatPlotsDiskFree.__table__


class StatPlotsDiskFreeQueryArgsSchema(Schema):
    id = ma.fields.Str()
    hostname = ma.fields.Str()

class BatchOfStatPlotsDiskFreeSchema(TopLevelSchema):
    _toplevel = ma.fields.Nested(
        StatPlotsDiskFreeSchema,
        required=True,
        many=True
    )

class BatchOfStatPlotsDiskFreeQueryArgsSchema(Schema):
    hostname = ma.fields.Str()
