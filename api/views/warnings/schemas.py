import marshmallow as ma
from marshmallow_sqlalchemy import field_for
from marshmallow_toplevel import TopLevelSchema

from api.extensions.api import Schema, AutoSchema
from common.models.warnings import Warning

class WarningSchema(AutoSchema):
    hostname = field_for(Warning, "hostname")
    blockchain = field_for(Warning, "blockchain")
    type = field_for(Warning, "type")

    class Meta(AutoSchema.Meta):
        table = Warning.__table__


class WarningQueryArgsSchema(Schema):
    hostname = ma.fields.Str()
    blockchain = ma.fields.Str()
    type = ma.fields.Str()

class BatchOfWarningSchema(TopLevelSchema):
    _toplevel = ma.fields.Nested(
        WarningSchema,
        required=True,
        many=True
    )

class BatchOfWarningQueryArgsSchema(Schema):
    hostname = ma.fields.Str()
    blockchain = ma.fields.Str()
    type = ma.fields.Str()
