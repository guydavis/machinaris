import datetime as dt

from flask.views import MethodView

from api import app
from api.extensions.api import Blueprint, SQLCursorPage
from common.extensions.database import db
from common.models import StatTimeToWin

from .schemas import StatTimeToWinSchema, StatTimeToWinQueryArgsSchema, BatchOfStatTimeToWinSchema, BatchOfStatTimeToWinQueryArgsSchema


blp = Blueprint(
    'StatTimeToWin',
    __name__,
    url_prefix='/stats/timetowin',
    description="Operations on stat timetowin recorded on each worker."
)


@blp.route('/')
class StatTimeToWins(MethodView):

    @blp.etag
    @blp.arguments(BatchOfStatTimeToWinQueryArgsSchema, location='query')
    @blp.response(200, StatTimeToWinSchema(many=True))
    @blp.paginate(SQLCursorPage)
    def get(self, args):
        ret = db.session.query(StatTimeToWin).filter_by(**args)
        return ret

    @blp.etag
    @blp.arguments(BatchOfStatTimeToWinSchema)
    @blp.response(201, StatTimeToWinSchema(many=True))
    def post(self, new_items):
        if len(new_items) == 0:
            return "No stats provided.", 400
        db.session.query(StatTimeToWin).filter(StatTimeToWin.hostname==new_items[0]['hostname'],
            StatTimeToWin.blockchain==new_items[0]['blockchain']).delete()
        items = []
        for new_item in new_items:
            item = StatTimeToWin(**new_item)
            items.append(item)
            db.session.add(item)
        db.session.commit()
        return items
