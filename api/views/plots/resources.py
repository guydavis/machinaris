import datetime as dt

from flask.views import MethodView

from api import app
from api.extensions.api import Blueprint, SQLCursorPage
from common.extensions.database import db
from common.models import Plot

from .schemas import PlotSchema, PlotQueryArgsSchema


blp = Blueprint(
    'Plots',
    __name__,
    url_prefix='/plots',
    description="Operations on plots"
)


@blp.route('/')
class Plots(MethodView):

    @blp.etag
    @blp.arguments(PlotQueryArgsSchema, location='query')
    @blp.response(200, PlotSchema(many=True))
    @blp.paginate(SQLCursorPage)
    def get(self, args):
        ret = Plot.query.filter_by(**args)
        return ret

    @blp.etag
    @blp.arguments(PlotSchema)
    @blp.response(201, PlotSchema)
    def post(self, new_item):
        item = Plot.query.get(new_item['plot_id'])
        if item: # upsert
            app.logger.info("item: {0}".format(item))
            app.logger.info("new_item: {0}".format(new_item))
            new_item['created_at'] = item.created_at
            new_item['updated_at'] = dt.datetime.now()
            PlotSchema().update(item, new_item)
        else: # insert
            item = Plot(**new_item)
        db.session.add(item)
        db.session.commit()
        return item


@blp.route('/<plot_id>')
class PlotsByPlotId(MethodView):

    @blp.etag
    @blp.response(200, PlotSchema)
    def get(self, plot_id):
        return Plot.query.get_or_404(plot_id)

    @blp.etag
    @blp.arguments(PlotSchema)
    @blp.response(200, PlotSchema)
    def put(self, new_item, plot_id):
        app.logger.info("new_item: {0}".format(new_item))
        item = Plot.query.get_or_404(plot_id)
        new_item['plot_id'] = item.plot_id
        new_item['created_at'] = item.created_at
        new_item['updated_at'] = dt.datetime.now()
        blp.check_etag(item, PlotSchema)
        PlotSchema().update(item, new_item)
        db.session.add(item)
        db.session.commit()
        return item

    @blp.etag
    @blp.response(204)
    def delete(self, plot_id):
        item = Plot.query.get_or_404(plot_id)
        blp.check_etag(item, PlotSchema)
        db.session.delete(item)
        db.session.commit()
