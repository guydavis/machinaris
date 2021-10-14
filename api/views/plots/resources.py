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
        # Re-enabled as Chives must send plots from each container
        items = []
        for new_item in new_items:
            app.logger.info(new_item)
            # Skip any previously sent by existing plot_id
            if not db.session.query(Plot).filter(Plot.hostname==new_item['hostname'], 
                Plot.plot_id==new_item['plot_id']).first():
                item = Plot(**new_item)
                items.append(item)
                db.session.add(item)
        db.session.commit()
        return items


@blp.route('/<hostname>/<blockchain>')
class PlotByHostname(MethodView):

    @blp.etag
    @blp.response(200, PlotSchema)
    def get(self, hostname, blockchain):
        return db.session.query(Plot).filter(Plot.hostname==hostname, Plot.blockchain==blockchain)

    @blp.etag
    @blp.arguments(BatchOfPlotSchema)
    @blp.response(200, PlotSchema(many=True))
    def put(self, new_items, hostname, blockchain):
        # Re-enabled as Chives must send plots from each container
        items = []
        for new_item in new_items:
            app.logger.info(new_item)
            # Skip any previously sent by existing plot_id
            if not db.session.query(Plot).filter(Plot.hostname==new_item['hostname'], 
                Plot.plot_id==new_item['plot_id']).first():
                item = Plot(**new_item)
                items.append(item)
                db.session.add(item)
        db.session.commit()
        return items

    @blp.etag
    @blp.response(204)
    def delete(self, hostname, blockchain):
        db.session.query(Plot).filter(Plot.hostname==hostname, Plot.blockchain==blockchain).delete()
        db.session.commit()
