import asyncio
import datetime as dt

from flask.views import MethodView

from api import app
from api.rpc import chia
from api.extensions.api import Blueprint, SQLCursorPage
from common.extensions.database import db
from common.models import Plot

from .schemas import PlotSchema, PlotQueryArgsSchema, BatchOfPlotSchema, BatchOfPlotQueryArgsSchema

blp = Blueprint(
    'Plot',
    __name__,
    url_prefix='/plots',
    description="Operations on all plots on farmer"
)

@blp.route('/')
class Plots(MethodView):

    @blp.etag
    @blp.arguments(BatchOfPlotQueryArgsSchema, location='query')
    @blp.response(200, PlotSchema(many=True))
    @blp.paginate(SQLCursorPage)
    def get(self, args):
        ret = db.session.query(Plot).filter_by(**args)
        return ret

    @blp.etag
    @blp.arguments(BatchOfPlotSchema)
    @blp.response(201, PlotSchema(many=True))
    def post(self, new_items):
        # Reworked status_plots.py to load directly on Controller after Flax updated to v0.1.1
        items = []
        return items


@blp.route('/<hostname>')
class PlotByHostname(MethodView):

    @blp.etag
    @blp.response(200, PlotSchema)
    def get(self, hostname):
        return db.session.query(Plot).filter(Plot.hostname==hostname)

    @blp.etag
    @blp.arguments(BatchOfPlotSchema)
    @blp.response(200, PlotSchema(many=True))
    def put(self, new_items, hostname):
        # Reworked status_plots.py to load directly on Controller after Flax updated to v0.1.1
        items = []
        return items

    @blp.etag
    @blp.response(204)
    def delete(self, hostname):
        db.session.query(Plot).filter(Plot.hostname==hostname).delete()
        db.session.commit()
