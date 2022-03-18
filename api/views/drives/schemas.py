import marshmallow as ma
from marshmallow_sqlalchemy import field_for
from marshmallow_toplevel import TopLevelSchema

from api.extensions.api import Schema, AutoSchema
from common.models.drives import Drive

class DriveSchema(AutoSchema):
    serial_number = field_for(Drive, "serial_number")

    class Meta(AutoSchema.Meta):
        table = Drive.__table__


class DriveQueryArgsSchema(Schema):
    serial_number = ma.fields.Str()
    hostname = ma.fields.Str()

class BatchOfDriveSchema(TopLevelSchema):
    _toplevel = ma.fields.Nested(
        DriveSchema,
        required=True,
        many=True
    )

class BatchOfDriveQueryArgsSchema(Schema):
    hostname = ma.fields.Str()
