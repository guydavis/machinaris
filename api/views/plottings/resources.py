import datetime as dt

from flask.views import MethodView

from api import app
from api.extensions.api import Blueprint, SQLCursorPage
from api.extensions.database import db
from api.models import Plotting

from .schemas import PlottingSchema, PlottingQueryArgsSchema


blp = Blueprint(
    'Plotting',
    __name__,
    url_prefix='/plottings',
    description="Operations on plots"
)


@blp.route('/')
class Plottings(MethodView):

    @blp.etag
    @blp.arguments(PlottingQueryArgsSchema, location='query')
    @blp.response(200, PlottingSchema(many=True))
    @blp.paginate(SQLCursorPage)
    def get(self, args):
        ret = Plotting.query.filter_by(**args)
        return ret

    @blp.etag
    @blp.arguments(PlottingSchema)
    @blp.response(201, PlottingSchema)
    def post(self, new_item):
        item = Plotting.query.get(new_item['plot_id'])
        if item: # upsert
            app.logger.info("item: {0}".format(item))
            app.logger.info("new_item: {0}".format(new_item))
            new_item['created_at'] = item.created_at
            new_item['updated_at'] = dt.datetime.now()
            PlottingSchema().update(item, new_item)
        else: # insert
            item = Plotting(**new_item)
        db.session.add(item)
        db.session.commit()
        return item


@blp.route('/<plot_id>')
class PlottingByPlotId(MethodView):

    @blp.etag
    @blp.response(200, PlottingSchema)
    def get(self, plot_id):
        return Plotting.query.get_or_404(plot_id)

    @blp.etag
    @blp.arguments(PlottingSchema)
    @blp.response(200, PlottingSchema)
    def put(self, new_item, plot_id):
        app.logger.info("new_item: {0}".format(new_item))
        item = Plotting.query.get_or_404(plot_id)
        new_item['plot_id'] = item.plot_id
        new_item['created_at'] = item.created_at
        new_item['updated_at'] = dt.datetime.now()
        blp.check_etag(item, PlottingSchema)
        PlottingSchema().update(item, new_item)
        db.session.add(item)
        db.session.commit()
        return item

    @blp.etag
    @blp.response(204)
    def delete(self, plot_id):
        item = Plotting.query.get_or_404(plot_id)
        blp.check_etag(item, PlottingSchema)
        db.session.delete(item)
        db.session.commit()
