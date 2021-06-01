import marshmallow as ma
from marshmallow_sqlalchemy import field_for

from api.extensions.api import Schema, AutoSchema
from api.models.plots import Plot


class PlotSchema(AutoSchema):
    plot_id = field_for(Plot, "plot_id")

    class Meta(AutoSchema.Meta):
        table = Plot.__table__


class PlotQueryArgsSchema(Schema):
    plot_id = ma.fields.Str()
    hostname = ma.fields.Str()
    dir = ma.fields.Str()
    file = ma.fields.Str()
    size = ma.fields.Int()
    