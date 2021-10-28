import datetime as dt

from flask.views import MethodView

from api import app
from api.extensions.api import Blueprint, SQLCursorPage
from common.extensions.database import db
from common.models import StatTotalChia

from .schemas import StatTotalChiaSchema, StatTotalChiaQueryArgsSchema, BatchOfStatTotalChiaSchema, BatchOfStatTotalChiaQueryArgsSchema


blp = Blueprint(
    'StatTotalChia',
    __name__,
    url_prefix='/stats/totalchia',
    description="Operations on stat totalchia recorded on each worker."
)


@blp.route('/')
class StatTotalChias(MethodView):

    @blp.etag
    @blp.arguments(BatchOfStatTotalChiaQueryArgsSchema, location='query')
    @blp.response(200, StatTotalChiaSchema(many=True))
    @blp.paginate(SQLCursorPage)
    def get(self, args):
        ret = db.session.query(StatTotalChia).filter_by(**args)
        return ret

    @blp.etag
    @blp.arguments(BatchOfStatTotalChiaSchema)
    @blp.response(201, StatTotalChiaSchema(many=True))
    def post(self, new_items):
        if len(new_items) == 0:
            return "No stats provided.", 400
        items = []
        for new_item in new_items:
            item = StatTotalChia(**new_item)
            items.append(item)
            db.session.add(item)
        db.session.commit()
        return items
