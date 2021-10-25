import marshmallow as ma
from marshmallow_sqlalchemy import field_for
from marshmallow_toplevel import TopLevelSchema

from api.extensions.api import Schema, AutoSchema
from common.models.stats import StatNetspaceSize

class StatNetspaceSizeSchema(AutoSchema):
    id = field_for(StatNetspaceSize, "id")

    class Meta(AutoSchema.Meta):
        table = StatNetspaceSize.__table__


class StatNetspaceSizeQueryArgsSchema(Schema):
    id = ma.fields.Str()
    hostname = ma.fields.Str()

class BatchOfStatNetspaceSizeSchema(TopLevelSchema):
    _toplevel = ma.fields.Nested(
        StatNetspaceSizeSchema,
        required=True,
        many=True
    )

class BatchOfStatNetspaceSizeQueryArgsSchema(Schema):
    hostname = ma.fields.Str()
