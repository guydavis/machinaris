import marshmallow as ma
from marshmallow_sqlalchemy import field_for

from api.extensions.api import Schema, AutoSchema
from api.models.alerts import Alert


class AlertSchema(AutoSchema):
    id = field_for(Alert, "id", dump_only=True)

    class Meta(AutoSchema.Meta):
        table = Alert.__table__


class AlertQueryArgsSchema(Schema):
    priority = ma.fields.Str()
    service = ma.fields.Str()
    message = ma.fields.Str()
