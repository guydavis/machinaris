import marshmallow as ma
from marshmallow_sqlalchemy import field_for
from marshmallow_toplevel import TopLevelSchema

from api.extensions.api import Schema, AutoSchema
from common.models.plottings import Plotting

class PlottingSchema(AutoSchema):
    plot_id = field_for(Plotting, "plot_id")

    class Meta(AutoSchema.Meta):
        table = Plotting.__table__


class PlottingQueryArgsSchema(Schema):
    plot_id = ma.fields.Str()
    hostname = ma.fields.Str()
    tmp = ma.fields.Str()
    dst = ma.fields.Str()
    size = ma.fields.Float()
    phase = ma.fields.Str()

class BatchOfPlottingSchema(TopLevelSchema):
    _toplevel = ma.fields.Nested(
        PlottingSchema,
        required=True,
        many=True
    )

class BatchOfPlottingQueryArgsSchema(Schema):
    hostname = ma.fields.Str()
