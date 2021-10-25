import datetime as dt

from flask.views import MethodView

from api import app
from api.extensions.api import Blueprint, SQLCursorPage
from common.extensions.database import db
from common.models import StatNetspaceSize

from .schemas import StatNetspaceSizeSchema, StatNetspaceSizeQueryArgsSchema, BatchOfStatNetspaceSizeSchema, BatchOfStatNetspaceSizeQueryArgsSchema


blp = Blueprint(
    'StatNetspaceSize',
    __name__,
    url_prefix='/stats/netspacesize',
    description="Operations on stat netspacesize recorded on each worker."
)


@blp.route('/')
class StatNetspaceSizes(MethodView):

    @blp.etag
    @blp.arguments(BatchOfStatNetspaceSizeQueryArgsSchema, location='query')
    @blp.response(200, StatNetspaceSizeSchema(many=True))
    @blp.paginate(SQLCursorPage)
    def get(self, args):
        ret = db.session.query(StatNetspaceSize).filter_by(**args)
        return ret

    @blp.etag
    @blp.arguments(BatchOfStatNetspaceSizeSchema)
    @blp.response(201, StatNetspaceSizeSchema(many=True))
    def post(self, new_items):
        if len(new_items) == 0:
            return "No stats provided.", 400
        db.session.query(StatNetspaceSize).filter(StatNetspaceSize.hostname==new_items[0]['hostname'],
            StatNetspaceSize.blockchain==new_items[0]['blockchain']).delete()
        items = []
        for new_item in new_items:
            item = StatNetspaceSize(**new_item)
            items.append(item)
            db.session.add(item)
        db.session.commit()
        return items
