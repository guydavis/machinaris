import datetime as dt

from flask.views import MethodView

from api import app
from api.extensions.api import Blueprint, SQLCursorPage
from common.extensions.database import db
from common.models import StatPlottingDiskUsed

from .schemas import StatPlottingDiskUsedSchema, StatPlottingDiskUsedQueryArgsSchema, BatchOfStatPlottingDiskUsedSchema, BatchOfStatPlottingDiskUsedQueryArgsSchema


blp = Blueprint(
    'StatPlottingDiskUsed',
    __name__,
    url_prefix='/stats/plottingdiskused',
    description="Operations on stat plottingdiskused recorded on each worker."
)


@blp.route('/')
class StatPlottingDiskUseds(MethodView):

    @blp.etag
    @blp.arguments(BatchOfStatPlottingDiskUsedQueryArgsSchema, location='query')
    @blp.response(200, StatPlottingDiskUsedSchema(many=True))
    @blp.paginate(SQLCursorPage)
    def get(self, args):
        ret = StatPlottingDiskUsed.query.filter_by(**args)
        return ret

    @blp.etag
    @blp.arguments(BatchOfStatPlottingDiskUsedSchema)
    @blp.response(201, StatPlottingDiskUsedSchema(many=True))
    def post(self, new_items):
        if len(new_items) == 0:
            return "No stats provided.", 400
        db.session.query(StatPlottingDiskUsed).filter(StatPlottingDiskUsed.hostname==new_items[0]['hostname']).delete()
        items = []
        for new_item in new_items:
            item = StatPlottingDiskUsed(**new_item)
            items.append(item)
            db.session.add(item)
        db.session.commit()
        return items


@blp.route('/<hostname>')
class StatPlottingDiskUsedByHostname(MethodView):

    @blp.etag
    @blp.response(200, StatPlottingDiskUsedSchema)
    def get(self, hostname):
        return db.session.query(StatPlottingDiskUsed).filter(StatPlottingDiskUsed.hostname==hostname)

    @blp.etag
    @blp.arguments(BatchOfStatPlottingDiskUsedSchema)
    @blp.response(200, StatPlottingDiskUsedSchema(many=True))
    def put(self, new_items, hostname):
        db.session.query(StatPlottingDiskUsed).filter(StatPlottingDiskUsed.hostname==hostname).delete()
        items = []
        for new_item in new_items:
            item = StatPlottingDiskUsed(**new_item)
            items.append(item)
            db.session.add(item)
        db.session.commit()
        return items

    @blp.etag
    @blp.response(204)
    def delete(self, hostname):
        db.session.query(StatPlottingDiskUsed).filter(StatPlottingDiskUsed.hostname==hostname).delete()
        db.session.commit()
