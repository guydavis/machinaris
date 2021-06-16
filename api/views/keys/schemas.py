import marshmallow as ma
from marshmallow_sqlalchemy import field_for

from api.extensions.api import Schema, AutoSchema
from common.models.keys import Key


class KeySchema(AutoSchema):
    hostname = field_for(Key, "hostname")

    class Meta(AutoSchema.Meta):
        table = Key.__table__


class KeyQueryArgsSchema(Schema):
    hostname = ma.fields.Str()
