import datetime as dt

from flask.views import MethodView

from api import app
from api.extensions.api import Blueprint, SQLCursorPage
from common.extensions.database import db
from common.models import StatPlottingDiskFree

from .schemas import StatPlottingDiskFreeSchema, StatPlottingDiskFreeQueryArgsSchema, BatchOfStatPlottingDiskFreeSchema, BatchOfStatPlottingDiskFreeQueryArgsSchema


blp = Blueprint(
    'StatPlottingDiskFree',
    __name__,
    url_prefix='/stats/plottingdiskfree',
    description="Operations on stat plottingdiskfree recorded on each worker."
)


@blp.route('/')
class StatPlottingDiskFrees(MethodView):

    @blp.etag
    @blp.arguments(BatchOfStatPlottingDiskFreeQueryArgsSchema, location='query')
    @blp.response(200, StatPlottingDiskFreeSchema(many=True))
    @blp.paginate(SQLCursorPage)
    def get(self, args):
        ret = StatPlottingDiskFree.query.filter_by(**args)
        return ret

    @blp.etag
    @blp.arguments(BatchOfStatPlottingDiskFreeSchema)
    @blp.response(201, StatPlottingDiskFreeSchema(many=True))
    def post(self, new_items):
        if len(new_items) == 0:
            return "No stats provided.", 400
        db.session.query(StatPlottingDiskFree).filter(StatPlottingDiskFree.hostname==new_items[0]['hostname']).delete()
        items = []
        for new_item in new_items:
            item = StatPlottingDiskFree(**new_item)
            items.append(item)
            db.session.add(item)
        db.session.commit()
        return items


@blp.route('/<hostname>')
class StatPlottingDiskFreeByHostname(MethodView):

    @blp.etag
    @blp.response(200, StatPlottingDiskFreeSchema)
    def get(self, hostname):
        return db.session.query(StatPlottingDiskFree).filter(StatPlottingDiskFree.hostname==hostname)

    @blp.etag
    @blp.arguments(BatchOfStatPlottingDiskFreeSchema)
    @blp.response(200, StatPlottingDiskFreeSchema(many=True))
    def put(self, new_items, hostname):
        db.session.query(StatPlottingDiskFree).filter(StatPlottingDiskFree.hostname==hostname).delete()
        items = []
        for new_item in new_items:
            item = StatPlottingDiskFree(**new_item)
            items.append(item)
            db.session.add(item)
        db.session.commit()
        return items

    @blp.etag
    @blp.response(204)
    def delete(self, hostname):
        db.session.query(StatPlottingDiskFree).filter(StatPlottingDiskFree.hostname==hostname).delete()
        db.session.commit()
