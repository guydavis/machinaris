import datetime as dt

from flask.views import MethodView

from api import app
from api.extensions.api import Blueprint, SQLCursorPage
from common.extensions.database import db
from common.models import Plotting

from .schemas import PlottingSchema, PlottingQueryArgsSchema, BatchOfPlottingSchema, BatchOfPlottingQueryArgsSchema


blp = Blueprint(
    'Plotting',
    __name__,
    url_prefix='/plottings',
    description="Operations on all plottings happening on plotter"
)


@blp.route('/')
class Plottings(MethodView):

    @blp.etag
    @blp.arguments(BatchOfPlottingQueryArgsSchema, location='query')
    @blp.response(200, PlottingSchema(many=True))
    @blp.paginate(SQLCursorPage)
    def get(self, args):
        ret = db.session.query(Plotting).filter_by(**args)
        return ret

@blp.route('/<hostname>/<blockchain>')
class PlottingByHostname(MethodView):

    @blp.etag
    @blp.response(200, PlottingSchema)
    def get(self, hostname, blockchain):
        return db.session.query(Plotting).filter(Plotting.hostname==hostname, Plotting.blockchain==blockchain)

    @blp.etag
    @blp.arguments(BatchOfPlottingSchema)
    @blp.response(200, PlottingSchema(many=True))
    def post(self, new_items, hostname, blockchain):
        db.session.query(Plotting).filter(Plotting.hostname==hostname, Plotting.blockchain==blockchain).delete()
        items = []
        for new_item in new_items:
            item = Plotting(**new_item)
            items.append(item)
            db.session.add(item)
        db.session.commit()
        return items

    @blp.etag
    @blp.response(204)
    def delete(self, hostname, blockchain):
        db.session.query(Plotting).filter(Plotting.hostname==hostname, Plotting.blockchain==blockchain).delete()
        db.session.commit()
