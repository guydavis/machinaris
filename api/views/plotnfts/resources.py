import datetime as dt

from flask.views import MethodView

from api import app
from api.extensions.api import Blueprint, SQLCursorPage
from common.extensions.database import db
from common.models import Plotnft

from .schemas import PlotnftSchema, BatchOfPlotnftSchema

blp = Blueprint(
    'Plotnfts',
    __name__,
    url_prefix='/plotnfts',
    description="Operations on plotnfts"
)

@blp.route('/')
class Plotnfts(MethodView):

    @blp.arguments(BatchOfPlotnftSchema)
    @blp.response(201, PlotnftSchema(many=True))
    def post(self, new_items):
        items = []
        for new_item in new_items:
            item = db.session.query(Plotnft).filter(Plotnft.unique_id==new_item['unique_id']).first()            
            if item:
                new_item['created_at'] = item.created_at
                new_item['updated_at'] = dt.datetime.now()
                PlotnftSchema().update(item, new_item)
            else:
                item = Plotnft(**new_item)
            db.session.add(item)
        db.session.commit()
        return items

@blp.route('/<hostname>/<blockchain>')
class PlotNftByHostname(MethodView):

    @blp.etag
    @blp.response(200, PlotnftSchema)
    def get(self, hostname, blockchain):
        return db.session.query(Plotnft).filter(Plotnft.hostname==hostname, Plotnft.blockchain==blockchain)

    @blp.etag
    @blp.response(204)
    def delete(self, hostname, blockchain):
        db.session.query(Plotnft).filter(Plotnft.hostname==hostname, Plotnft.blockchain==blockchain).delete()
        db.session.commit()
