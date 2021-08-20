import marshmallow as ma
from marshmallow_sqlalchemy import field_for
from marshmallow_toplevel import TopLevelSchema

from api.extensions.api import Schema, AutoSchema
from common.models.stats import StatPlottingDiskUsed

class StatPlottingDiskUsedSchema(AutoSchema):
    id = field_for(StatPlottingDiskUsed, "id")

    class Meta(AutoSchema.Meta):
        table = StatPlottingDiskUsed.__table__


class StatPlottingDiskUsedQueryArgsSchema(Schema):
    id = ma.fields.Str()
    hostname = ma.fields.Str()

class BatchOfStatPlottingDiskUsedSchema(TopLevelSchema):
    _toplevel = ma.fields.Nested(
        StatPlottingDiskUsedSchema,
        required=True,
        many=True
    )

class BatchOfStatPlottingDiskUsedQueryArgsSchema(Schema):
    hostname = ma.fields.Str()
