import marshmallow as ma
from marshmallow_sqlalchemy import field_for

from api.extensions.api import Schema, AutoSchema
from api.models.farms import Farm


class FarmSchema(AutoSchema):
    hostname = field_for(Farm, "hostname")

    class Meta(AutoSchema.Meta):
        table = Farm.__table__


class FarmQueryArgsSchema(Schema):
    hostname = ma.fields.Str()
    plot_count = ma.fields.Str()
    plot_size = ma.fields.Str()
