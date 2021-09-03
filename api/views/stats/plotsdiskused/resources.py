import datetime as dt

from flask.views import MethodView

from api import app
from api.extensions.api import Blueprint, SQLCursorPage
from common.extensions.database import db
from common.models import StatPlotsDiskUsed

from .schemas import StatPlotsDiskUsedSchema, StatPlotsDiskUsedQueryArgsSchema, BatchOfStatPlotsDiskUsedSchema, BatchOfStatPlotsDiskUsedQueryArgsSchema


blp = Blueprint(
    'StatPlotsDiskUsed',
    __name__,
    url_prefix='/stats/plotsdiskused',
    description="Operations on stat plotsdiskused recorded on each worker."
)


@blp.route('/')
class StatPlotsDiskUseds(MethodView):

    @blp.etag
    @blp.arguments(BatchOfStatPlotsDiskUsedQueryArgsSchema, location='query')
    @blp.response(200, StatPlotsDiskUsedSchema(many=True))
    @blp.paginate(SQLCursorPage)
    def get(self, args):
        ret = db.session.query(StatPlotsDiskUsed).filter_by(**args)
        return ret

    @blp.etag
    @blp.arguments(BatchOfStatPlotsDiskUsedSchema)
    @blp.response(201, StatPlotsDiskUsedSchema(many=True))
    def post(self, new_items):
        if len(new_items) == 0:
            return "No stats provided.", 400
        db.session.query(StatPlotsDiskUsed).filter(StatPlotsDiskUsed.hostname==new_items[0]['hostname']).delete()
        items = []
        for new_item in new_items:
            item = StatPlotsDiskUsed(**new_item)
            items.append(item)
            db.session.add(item)
        db.session.commit()
        return items


@blp.route('/<hostname>')
class StatPlotsDiskUsedByHostname(MethodView):

    @blp.etag
    @blp.response(200, StatPlotsDiskUsedSchema)
    def get(self, hostname):
        return db.session.query(StatPlotsDiskUsed).filter(StatPlotsDiskUsed.hostname==hostname)

    @blp.etag
    @blp.arguments(BatchOfStatPlotsDiskUsedSchema)
    @blp.response(200, StatPlotsDiskUsedSchema(many=True))
    def put(self, new_items, hostname):
        db.session.query(StatPlotsDiskUsed).filter(StatPlotsDiskUsed.hostname==hostname).delete()
        items = []
        for new_item in new_items:
            item = StatPlotsDiskUsed(**new_item)
            items.append(item)
            db.session.add(item)
        db.session.commit()
        return items

    @blp.etag
    @blp.response(204)
    def delete(self, hostname):
        db.session.query(StatPlotsDiskUsed).filter(StatPlotsDiskUsed.hostname==hostname).delete()
        db.session.commit()
