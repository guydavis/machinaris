import datetime as dt

from flask.views import MethodView

from api import app
from api.extensions.api import Blueprint, SQLCursorPage
from common.extensions.database import db
from common.models import StatPlotsDiskFree

from .schemas import StatPlotsDiskFreeSchema, StatPlotsDiskFreeQueryArgsSchema, BatchOfStatPlotsDiskFreeSchema, BatchOfStatPlotsDiskFreeQueryArgsSchema


blp = Blueprint(
    'StatPlotsDiskFree',
    __name__,
    url_prefix='/stats/plotsdiskfree',
    description="Operations on stat plotsdiskfree recorded on each worker."
)


@blp.route('/')
class StatPlotsDiskFrees(MethodView):

    @blp.etag
    @blp.arguments(BatchOfStatPlotsDiskFreeQueryArgsSchema, location='query')
    @blp.response(200, StatPlotsDiskFreeSchema(many=True))
    @blp.paginate(SQLCursorPage)
    def get(self, args):
        ret = StatPlotsDiskFree.query.filter_by(**args)
        return ret

    @blp.etag
    @blp.arguments(BatchOfStatPlotsDiskFreeSchema)
    @blp.response(201, StatPlotsDiskFreeSchema(many=True))
    def post(self, new_items):
        if len(new_items) == 0:
            return "No stats provided.", 400
        db.session.query(StatPlotsDiskFree).filter(StatPlotsDiskFree.hostname==new_items[0]['hostname']).delete()
        items = []
        for new_item in new_items:
            item = StatPlotsDiskFree(**new_item)
            items.append(item)
            db.session.add(item)
        db.session.commit()
        return items


@blp.route('/<hostname>')
class StatPlotsDiskFreeByHostname(MethodView):

    @blp.etag
    @blp.response(200, StatPlotsDiskFreeSchema)
    def get(self, hostname):
        return db.session.query(StatPlotsDiskFree).filter(StatPlotsDiskFree.hostname==hostname)

    @blp.etag
    @blp.arguments(BatchOfStatPlotsDiskFreeSchema)
    @blp.response(200, StatPlotsDiskFreeSchema(many=True))
    def put(self, new_items, hostname):
        db.session.query(StatPlotsDiskFree).filter(StatPlotsDiskFree.hostname==hostname).delete()
        items = []
        for new_item in new_items:
            item = StatPlotsDiskFree(**new_item)
            items.append(item)
            db.session.add(item)
        db.session.commit()
        return items

    @blp.etag
    @blp.response(204)
    def delete(self, hostname):
        db.session.query(StatPlotsDiskFree).filter(StatPlotsDiskFree.hostname==hostname).delete()
        db.session.commit()
