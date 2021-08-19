import marshmallow as ma
from marshmallow_sqlalchemy import field_for
from marshmallow_toplevel import TopLevelSchema

from api.extensions.api import Schema, AutoSchema
from common.models.stats import StatPlotsDiskUsed

class StatPlotsDiskUsedSchema(AutoSchema):
    id = field_for(StatPlotsDiskUsed, "id")

    class Meta(AutoSchema.Meta):
        table = StatPlotsDiskUsed.__table__


class StatPlotsDiskUsedQueryArgsSchema(Schema):
    id = ma.fields.Str()
    hostname = ma.fields.Str()

class BatchOfStatPlotsDiskUsedSchema(TopLevelSchema):
    _toplevel = ma.fields.Nested(
        StatPlotsDiskUsedSchema,
        required=True,
        many=True
    )

class BatchOfStatPlotsDiskUsedQueryArgsSchema(Schema):
    hostname = ma.fields.Str()
