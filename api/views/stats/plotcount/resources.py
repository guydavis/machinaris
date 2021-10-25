import datetime as dt

from flask.views import MethodView

from api import app
from api.extensions.api import Blueprint, SQLCursorPage
from common.extensions.database import db
from common.models import StatPlotCount

from .schemas import StatPlotCountSchema, StatPlotCountQueryArgsSchema, BatchOfStatPlotCountSchema, BatchOfStatPlotCountQueryArgsSchema


blp = Blueprint(
    'StatPlotCount',
    __name__,
    url_prefix='/stats/plotcount',
    description="Operations on stat plotcount recorded on each worker."
)


@blp.route('/')
class StatPlotCounts(MethodView):

    @blp.etag
    @blp.arguments(BatchOfStatPlotCountQueryArgsSchema, location='query')
    @blp.response(200, StatPlotCountSchema(many=True))
    @blp.paginate(SQLCursorPage)
    def get(self, args):
        ret = db.session.query(StatPlotCount).filter_by(**args)
        return ret

    @blp.etag
    @blp.arguments(BatchOfStatPlotCountSchema)
    @blp.response(201, StatPlotCountSchema(many=True))
    def post(self, new_items):
        if len(new_items) == 0:
            return "No stats provided.", 400
        db.session.query(StatPlotCount).filter(StatPlotCount.hostname==new_items[0]['hostname'],
            StatPlotCount.blockchain==new_items[0]['blockchain']).delete()
        items = []
        for new_item in new_items:
            item = StatPlotCount(**new_item)
            items.append(item)
            db.session.add(item)
        db.session.commit()
        return items
