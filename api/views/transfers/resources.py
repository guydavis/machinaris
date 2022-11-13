import datetime as dt

from flask.views import MethodView

from api import app
from api.extensions.api import Blueprint, SQLCursorPage
from common.extensions.database import db
from common.models import Transfer

from .schemas import TransferSchema, TransferQueryArgsSchema, BatchOfTransferSchema, BatchOfTransferQueryArgsSchema


blp = Blueprint(
    'Transfer',
    __name__,
    url_prefix='/transfers',
    description="Operations on all transfers happening by archiver"
)


@blp.route('/')
class Transfers(MethodView):

    @blp.etag
    @blp.arguments(BatchOfTransferQueryArgsSchema, location='query')
    @blp.response(200, TransferSchema(many=True))
    @blp.paginate(SQLCursorPage)
    def get(self, args):
        ret = db.session.query(Transfer).filter_by(**args)
        return ret

@blp.route('/<hostname>/<blockchain>')
class TransferByHostname(MethodView):

    @blp.etag
    @blp.response(200, TransferSchema)
    def get(self, hostname, blockchain):
        return db.session.query(Transfer).filter(Transfer.hostname==hostname, Transfer.blockchain==blockchain)

    @blp.etag
    @blp.arguments(BatchOfTransferSchema)
    @blp.response(200, TransferSchema(many=True))
    def post(self, new_items, hostname, blockchain):
        db.session.query(Transfer).filter(Transfer.hostname==hostname, Transfer.blockchain==blockchain).delete()
        items = []
        for new_item in new_items:
            item = Transfer(**new_item)
            items.append(item)
            db.session.add(item)
        db.session.commit()
        return items

    @blp.etag
    @blp.response(204)
    def delete(self, hostname, blockchain):
        db.session.query(Transfer).filter(Transfer.hostname==hostname, Transfer.blockchain==blockchain).delete()
        db.session.commit()
