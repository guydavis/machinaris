import marshmallow as ma
from marshmallow_sqlalchemy import field_for

from api.extensions.api import Schema, AutoSchema
from common.models.plotnfts import Plotnft

class PlotnftSchema(AutoSchema):
    hostname = field_for(Plotnft, "hostname")

    class Meta(AutoSchema.Meta):
        table = Plotnft.__table__


class PlotnftQueryArgsSchema(Schema):
    hostname = ma.fields.Str()
