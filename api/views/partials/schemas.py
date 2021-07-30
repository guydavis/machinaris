import marshmallow as ma
from marshmallow_sqlalchemy import field_for
from marshmallow_toplevel import TopLevelSchema

from api.extensions.api import Schema, AutoSchema
from common.models.partials import Partial

class PartialSchema(AutoSchema):
    unique_id = field_for(Partial, "unique_id")

    class Meta(AutoSchema.Meta):
        table = Partial.__table__


class PartialQueryArgsSchema(Schema):
    unique_id = ma.fields.Str()
    hostname = ma.fields.Str()

class BatchOfPartialSchema(TopLevelSchema):
    _toplevel = ma.fields.Nested(
        PartialSchema,
        required=True,
        many=True
    )

class BatchOfPartialQueryArgsSchema(Schema):
    hostname = ma.fields.Str()
