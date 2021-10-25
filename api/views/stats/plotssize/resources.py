import datetime as dt

from flask.views import MethodView

from api import app
from api.extensions.api import Blueprint, SQLCursorPage
from common.extensions.database import db
from common.models import StatPlotsSize

from .schemas import StatPlotsSizeSchema, StatPlotsSizeQueryArgsSchema, BatchOfStatPlotsSizeSchema, BatchOfStatPlotsSizeQueryArgsSchema


blp = Blueprint(
    'StatPlotsSize',
    __name__,
    url_prefix='/stats/plotssize',
    description="Operations on stat plotssize recorded on each worker."
)


@blp.route('/')
class StatPlotsSizes(MethodView):

    @blp.etag
    @blp.arguments(BatchOfStatPlotsSizeQueryArgsSchema, location='query')
    @blp.response(200, StatPlotsSizeSchema(many=True))
    @blp.paginate(SQLCursorPage)
    def get(self, args):
        ret = db.session.query(StatPlotsSize).filter_by(**args)
        return ret

    @blp.etag
    @blp.arguments(BatchOfStatPlotsSizeSchema)
    @blp.response(201, StatPlotsSizeSchema(many=True))
    def post(self, new_items):
        if len(new_items) == 0:
            return "No stats provided.", 400
        db.session.query(StatPlotsSize).filter(StatPlotsSize.hostname==new_items[0]['hostname'],
            StatPlotsSize.blockchain==new_items[0]['blockchain']).delete()
        items = []
        for new_item in new_items:
            item = StatPlotsSize(**new_item)
            items.append(item)
            db.session.add(item)
        db.session.commit()
        return items
