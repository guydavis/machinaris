import marshmallow as ma
from marshmallow_sqlalchemy import field_for
from marshmallow_toplevel import TopLevelSchema

from api.extensions.api import Schema, AutoSchema
from common.models.plotnfts import Plotnft

class PlotnftSchema(AutoSchema):
    unique_id = field_for(Plotnft, "unique_id")

    class Meta(AutoSchema.Meta):
        table = Plotnft.__table__

class PlotnftQueryArgsSchema(Schema):
    hostname = ma.fields.Str()

class BatchOfPlotnftSchema(TopLevelSchema):
    _toplevel = ma.fields.Nested(
        PlotnftSchema,
        required=True,
        many=True
    )

class BatchOfPlotnftsQueryArgsSchema(Schema):
    unique_id = ma.fields.Str()
