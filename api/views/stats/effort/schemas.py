import marshmallow as ma
from marshmallow_sqlalchemy import field_for
from marshmallow_toplevel import TopLevelSchema

from api.extensions.api import Schema, AutoSchema
from common.models.stats import StatEffort

class StatEffortSchema(AutoSchema):
    id = field_for(StatEffort, "id")

    class Meta(AutoSchema.Meta):
        table = StatEffort.__table__


class StatEffortQueryArgsSchema(Schema):
    id = ma.fields.Str()
    hostname = ma.fields.Str()

class BatchOfStatEffortSchema(TopLevelSchema):
    _toplevel = ma.fields.Nested(
        StatEffortSchema,
        required=True,
        many=True
    )

class BatchOfStatEffortQueryArgsSchema(Schema):
    hostname = ma.fields.Str()
