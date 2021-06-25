import marshmallow as ma
from marshmallow_sqlalchemy import field_for
from marshmallow_toplevel import TopLevelSchema

from api.extensions.api import Schema, AutoSchema
from common.models.alerts import Alert

class AlertSchema(AutoSchema):
    unique_id = field_for(Alert, "unique_id")

    class Meta(AutoSchema.Meta):
        table = Alert.__table__


class AlertQueryArgsSchema(Schema):
    unique_id = ma.fields.Str()
    hostname = ma.fields.Str()
    tmp = ma.fields.Str()
    dst = ma.fields.Str()
    size = ma.fields.Float()
    created_at = ma.fields.Str()

class BatchOfAlertSchema(TopLevelSchema):
    _toplevel = ma.fields.Nested(
        AlertSchema,
        required=True,
        many=True
    )

class BatchOfAlertQueryArgsSchema(Schema):
    hostname = ma.fields.Str()
