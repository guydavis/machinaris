import marshmallow as ma
from marshmallow_sqlalchemy import field_for
from marshmallow_toplevel import TopLevelSchema

from api.extensions.api import Schema, AutoSchema
from common.models.plots import Plot

class PlotSchema(AutoSchema):
    plot_id = field_for(Plot, "plot_id")

    class Meta(AutoSchema.Meta):
        table = Plot.__table__


class PlotQueryArgsSchema(Schema):
    plot_id = ma.fields.Str()
    hostname = ma.fields.Str()
    tmp = ma.fields.Str()
    dst = ma.fields.Str()
    size = ma.fields.Float()
    created_at = ma.fields.Str()

class BatchOfPlotSchema(TopLevelSchema):
    _toplevel = ma.fields.Nested(
        PlotSchema,
        required=True,
        many=True
    )

class BatchOfPlotQueryArgsSchema(Schema):
    hostname = ma.fields.Str()
