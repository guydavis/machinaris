import marshmallow as ma
from marshmallow_sqlalchemy import field_for
from marshmallow_toplevel import TopLevelSchema

from api.extensions.api import Schema, AutoSchema
from common.models.transfers import Transfer

class TransferSchema(AutoSchema):
    log_file = field_for(Transfer, "log_file")

    class Meta(AutoSchema.Meta):
        table = Transfer.__table__


class TransferQueryArgsSchema(Schema):
    log_file = ma.fields.Str()
    blockchain = ma.fields.Str()
    hostname = ma.fields.Str()
    plot_id = ma.fields.Str()

class BatchOfTransferSchema(TopLevelSchema):
    _toplevel = ma.fields.Nested(
        TransferSchema,
        required=True,
        many=True
    )

class BatchOfTransferQueryArgsSchema(Schema):
    hostname = ma.fields.Str()
