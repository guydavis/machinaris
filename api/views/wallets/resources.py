import datetime as dt

from flask.views import MethodView

from api import app
from api.extensions.api import Blueprint, SQLCursorPage
from common.extensions.database import db
from common.models import Wallet

from .schemas import WalletSchema, WalletQueryArgsSchema


blp = Blueprint(
    'Wallets',
    __name__,
    url_prefix='/wallets',
    description="Operations on wallets"
)


@blp.route('/')
class Wallets(MethodView):

    @blp.etag
    @blp.arguments(WalletQueryArgsSchema, location='query')
    @blp.response(200, WalletSchema(many=True))
    @blp.paginate(SQLCursorPage)
    def get(self, args):
        return Wallet.query.filter_by(**args)

    @blp.etag
    @blp.arguments(WalletSchema)
    @blp.response(201, WalletSchema)
    def post(self, new_item):
        item = Wallet.query.get(new_item['hostname'])
        if item: # upsert
            new_item['created_at'] = item.created_at
            new_item['updated_at'] = dt.datetime.now()
            WalletSchema().update(item, new_item)
        else: # insert
            item = Wallet(**new_item)
        db.session.add(item)
        db.session.commit()
        return item


@blp.route('/<hostname>')
class WalletsByHostname(MethodView):

    @blp.etag
    @blp.response(200, WalletSchema)
    def get(self, hostname):
        return Wallet.query.get_or_404(hostname)

    @blp.etag
    @blp.arguments(WalletSchema)
    @blp.response(200, WalletSchema)
    def put(self, new_item, hostname):
        item = Wallet.query.get_or_404(hostname)
        new_item['hostname'] = item.hostname
        new_item['created_at'] = item.created_at
        new_item['updated_at'] = dt.datetime.now()
        blp.check_etag(item, WalletSchema)
        WalletSchema().update(item, new_item)
        db.session.add(item)
        db.session.commit()
        return item

    @blp.etag
    @blp.response(204)
    def delete(self, hostname):
        item = Wallet.query.get_or_404(hostname)
        blp.check_etag(item, WalletSchema)
        db.session.delete(item)
        db.session.commit()