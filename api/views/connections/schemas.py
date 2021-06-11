import marshmallow as ma
from marshmallow_sqlalchemy import field_for

from api.extensions.api import Schema, AutoSchema
from common.models.connections import Connection


class ConnectionSchema(AutoSchema):
    hostname = field_for(Connection, "hostname")

    class Meta(AutoSchema.Meta):
        table = Connection.__table__


class ConnectionQueryArgsSchema(Schema):
    hostname = ma.fields.Str()
