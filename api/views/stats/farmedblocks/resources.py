import datetime as dt

from flask.views import MethodView

from api import app
from api.extensions.api import Blueprint, SQLCursorPage
from common.extensions.database import db
from common.models import StatFarmedBlocks

from .schemas import StatFarmedBlocksSchema, StatFarmedBlocksQueryArgsSchema, BatchOfStatFarmedBlocksSchema, BatchOfStatFarmedBlocksQueryArgsSchema


blp = Blueprint(
    'StatFarmedBlocks',
    __name__,
    url_prefix='/stats/farmedblocks',
    description="Operations on stat farmedblocks recorded on each worker."
)


@blp.route('/')
class StatFarmedBlockss(MethodView):

    @blp.etag
    @blp.arguments(BatchOfStatFarmedBlocksQueryArgsSchema, location='query')
    @blp.response(200, StatFarmedBlocksSchema(many=True))
    @blp.paginate(SQLCursorPage)
    def get(self, args):
        ret = db.session.query(StatFarmedBlocks).filter_by(**args)
        return ret

    @blp.etag
    @blp.arguments(BatchOfStatFarmedBlocksSchema)
    @blp.response(201, StatFarmedBlocksSchema(many=True))
    def post(self, new_items):
        if len(new_items) == 0:
            return "No farmed blocks provided.", 400
        items = []
        for new_item in new_items:
            # Skip any previously sent by existing challenge_id from that host
            if not db.session.query(StatFarmedBlocks).filter(StatFarmedBlocks.hostname==new_item['hostname'], StatFarmedBlocks.challenge_id==new_item['challenge_id']).first():
                item = StatFarmedBlocks(**new_item)
                items.append(item)
                db.session.add(item)
        db.session.commit()
        return items
