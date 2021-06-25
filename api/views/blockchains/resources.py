import datetime as dt

from flask.views import MethodView

from api import app
from api.extensions.api import Blueprint, SQLCursorPage
from common.extensions.database import db
from common.models import Blockchain

from .schemas import BlockchainSchema, BlockchainQueryArgsSchema


blp = Blueprint(
    'Blockchains',
    __name__,
    url_prefix='/blockchains',
    description="Operations on blockchains"
)


@blp.route('/')
class Blockchains(MethodView):

    @blp.etag
    @blp.arguments(BlockchainQueryArgsSchema, location='query')
    @blp.response(200, BlockchainSchema(many=True))
    @blp.paginate(SQLCursorPage)
    def get(self, args):
        return Blockchain.query.filter_by(**args)

    @blp.etag
    @blp.arguments(BlockchainSchema)
    @blp.response(201, BlockchainSchema)
    def post(self, new_item):
        item = Blockchain.query.get(new_item['hostname'])
        if item: # upsert
            new_item['created_at'] = item.created_at
            new_item['updated_at'] = dt.datetime.now()
            BlockchainSchema().update(item, new_item)
        else: # insert
            item = Blockchain(**new_item)
        db.session.add(item)
        db.session.commit()
        return item


@blp.route('/<hostname>')
class BlockchainsByHostname(MethodView):

    @blp.etag
    @blp.response(200, BlockchainSchema)
    def get(self, hostname):
        return Blockchain.query.get_or_404(hostname)

    @blp.etag
    @blp.arguments(BlockchainSchema)
    @blp.response(200, BlockchainSchema)
    def put(self, new_item, hostname):
        item = Blockchain.query.get_or_404(hostname)
        new_item['hostname'] = item.hostname
        new_item['created_at'] = item.created_at
        new_item['updated_at'] = dt.datetime.now()
        blp.check_etag(item, BlockchainSchema)
        BlockchainSchema().update(item, new_item)
        db.session.add(item)
        db.session.commit()
        return item

    @blp.etag
    @blp.response(204)
    def delete(self, hostname):
        item = Blockchain.query.get_or_404(hostname)
        blp.check_etag(item, BlockchainSchema)
        db.session.delete(item)
        db.session.commit()