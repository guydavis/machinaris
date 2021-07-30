import marshmallow as ma
from marshmallow_sqlalchemy import field_for
from marshmallow_toplevel import TopLevelSchema

from api.extensions.api import Schema, AutoSchema
from common.models.pools import Pool

class PoolSchema(AutoSchema):
    unique_id = field_for(Pool, "unique_id")

    class Meta(AutoSchema.Meta):
        table = Pool.__table__


class PoolQueryArgsSchema(Schema):
    unique_id = ma.fields.Str()
    hostname = ma.fields.Str()

class BatchOfPoolSchema(TopLevelSchema):
    _toplevel = ma.fields.Nested(
        PoolSchema,
        required=True,
        many=True
    )

class BatchOfPoolQueryArgsSchema(Schema):
    hostname = ma.fields.Str()
