import marshmallow as ma
from marshmallow_sqlalchemy import field_for
from marshmallow_toplevel import TopLevelSchema

from api.extensions.api import Schema, AutoSchema
from common.models.stats import StatTotalChia

class StatTotalChiaSchema(AutoSchema):
    id = field_for(StatTotalChia, "id")

    class Meta(AutoSchema.Meta):
        table = StatTotalChia.__table__


class StatTotalChiaQueryArgsSchema(Schema):
    id = ma.fields.Str()
    hostname = ma.fields.Str()

class BatchOfStatTotalChiaSchema(TopLevelSchema):
    _toplevel = ma.fields.Nested(
        StatTotalChiaSchema,
        required=True,
        many=True
    )

class BatchOfStatTotalChiaQueryArgsSchema(Schema):
    hostname = ma.fields.Str()
