import marshmallow as ma
from marshmallow_sqlalchemy import field_for

from api.extensions.api import Schema, AutoSchema
from common.models.workers import Worker


class WorkerSchema(AutoSchema):
    hostname = field_for(Worker, "hostname")

    class Meta(AutoSchema.Meta):
        table = Worker.__table__


class WorkerQueryArgsSchema(Schema):
    hostname = ma.fields.Str()
    mode = ma.fields.Str()
    plotting = ma.fields.Str()
