import datetime as dt

from flask.views import MethodView

from api import app
from api.extensions.api import Blueprint, SQLCursorPage
from common.extensions.database import db
from common.models import Partial

from .schemas import PartialSchema, PartialQueryArgsSchema, BatchOfPartialSchema, BatchOfPartialQueryArgsSchema


blp = Blueprint(
    'Partial',
    __name__,
    url_prefix='/partials',
    description="Operations on all partials recorded on farmer"
)


@blp.route('/')
class Partials(MethodView):

    @blp.etag
    @blp.arguments(BatchOfPartialQueryArgsSchema, location='query')
    @blp.response(200, PartialSchema(many=True))
    @blp.paginate(SQLCursorPage)
    def get(self, args):
        ret = Partial.query.filter_by(**args)
        return ret

    @blp.etag
    @blp.arguments(BatchOfPartialSchema)
    @blp.response(201, PartialSchema(many=True))
    def post(self, new_items):
        if len(new_items) == 0:
            return "No partials provided.", 400
        items = []
        for new_item in new_items:
            item = Partial.query.get(new_item['unique_id'])
            if not item:  # Request contains previously received challenges, only add new
                item = Partial(**new_item)
                items.append(item)
                db.session.add(item)
            else:
                app.logger.info("Skipping insert of existing partial: {0}".format(new_item['unique_id']))
        db.session.commit()
        return items


@blp.route('/<hostname>/<blockchain>')
class PartialByHostname(MethodView):

    @blp.etag
    @blp.response(200, PartialSchema)
    def get(self, hostname, blockchain):
        return db.session.query(Partial).filter(Partial.hostname==hostname, Partial.blockchain==blockchain)

    @blp.etag
    @blp.arguments(BatchOfPartialSchema)
    @blp.response(200, PartialSchema(many=True))
    def put(self, new_items, hostname, blockchain):
        items = []
        for new_item in new_items:
            item = Partial.query.get(new_item['unique_id'])
            if not item:  # Request contains previously received challenges, only add new
                item = Partial(**new_item)
                items.append(item)
                db.session.add(item)
        db.session.commit()
        return items

    @blp.etag
    @blp.response(204)
    def delete(self, hostname, blockchain):
        db.session.query(Partial).filter(Partial.hostname==hostname, Partial.blockchain==blockchain).delete()
        db.session.commit()
