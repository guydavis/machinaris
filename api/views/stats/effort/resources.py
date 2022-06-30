import datetime as dt

from flask.views import MethodView

from api import app
from api.extensions.api import Blueprint, SQLCursorPage
from common.extensions.database import db
from common.models import StatEffort

from .schemas import StatEffortSchema, StatEffortQueryArgsSchema, BatchOfStatEffortSchema, BatchOfStatEffortQueryArgsSchema


blp = Blueprint(
    'StatEffort',
    __name__,
    url_prefix='/stats/effort',
    description="Operations on stat effort recorded on each worker."
)


@blp.route('/')
class StatEfforts(MethodView):

    @blp.etag
    @blp.arguments(BatchOfStatEffortQueryArgsSchema, location='query')
    @blp.response(200, StatEffortSchema(many=True))
    @blp.paginate(SQLCursorPage)
    def get(self, args):
        ret = db.session.query(StatEffort).filter_by(**args)
        return ret

    @blp.etag
    @blp.arguments(BatchOfStatEffortSchema)
    @blp.response(201, StatEffortSchema(many=True))
    def post(self, new_items):
        if len(new_items) == 0:
            return "No stats provided.", 400
        items = []
        for new_item in new_items:
            item = StatEffort(**new_item)
            items.append(item)
            db.session.add(item)
        db.session.commit()
        return items
