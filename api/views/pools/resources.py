import datetime as dt

from flask.views import MethodView

from api import app
from api.extensions.api import Blueprint, SQLCursorPage
from common.extensions.database import db
from common.models import Pool

from .schemas import PoolSchema, PoolQueryArgsSchema, BatchOfPoolSchema, BatchOfPoolQueryArgsSchema


blp = Blueprint(
    'Pool',
    __name__,
    url_prefix='/pools',
    description="Operations on all pools recorded on farmer"
)


@blp.route('/')
class Pools(MethodView):

    @blp.etag
    @blp.arguments(BatchOfPoolQueryArgsSchema, location='query')
    @blp.response(200, PoolSchema(many=True))
    @blp.paginate(SQLCursorPage)
    def get(self, args):
        ret = db.session.query(Pool).filter_by(**args)
        return ret

    @blp.etag
    @blp.arguments(BatchOfPoolSchema)
    @blp.response(201, PoolSchema(many=True))
    def post(self, new_items):
        if len(new_items) == 0:
            return "No pools provided.", 400
        db.session.query(Pool).filter(Pool.hostname==new_items[0]['hostname']).delete()
        items = []
        for new_item in new_items:
            item = Pool(**new_item)
            items.append(item)
            db.session.add(item)
        db.session.commit()
        return items


@blp.route('/<hostname>/<blockchain>')
class PoolByHostname(MethodView):

    @blp.etag
    @blp.response(200, PoolSchema)
    def get(self, hostname, blockchain):
        return db.session.query(Pool).filter(Pool.hostname==hostname, Pool.blockchain==blockchain)

    @blp.etag
    @blp.arguments(BatchOfPoolSchema)
    @blp.response(200, PoolSchema(many=True))
    def put(self, new_items, hostname, blockchain):
        db.session.query(Pool).filter(Pool.hostname==hostname, Pool.blockchain==blockchain).delete()
        items = []
        for new_item in new_items:
            item = Pool(**new_item)
            items.append(item)
            db.session.add(item)
        db.session.commit()
        return items

    @blp.etag
    @blp.response(204)
    def delete(self, hostname, blockchain):
        db.session.query(Pool).filter(Pool.hostname==hostname, Pool.blockchain==blockchain).delete()
        db.session.commit()
