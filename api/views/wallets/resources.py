import datetime as dt
import traceback

from flask.views import MethodView

from api import app
from api.commands.websvcs import cold_wallet_balance
from api.extensions.api import Blueprint, SQLCursorPage
from api.commands import websvcs
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
        return db.session.query(Wallet).filter_by(**args)

    @blp.etag
    @blp.arguments(WalletSchema)
    @blp.response(201, WalletSchema)
    def post(self, new_item):
        blockchain = new_item['blockchain']
        item = db.session.query(Wallet).filter(Wallet.hostname==new_item['hostname'], \
            Wallet.blockchain==blockchain).first()
        try:
            new_item['cold_balance'] = websvcs.cold_wallet_balance(blockchain)
        except Exception as ex:
            app.logger.error("Failed to get cold wallet balance for {0} due to {1}".format(blockchain, str(ex)))
        if item: # upsert
            new_item['created_at'] = item.created_at
            new_item['updated_at'] = dt.datetime.now()
            WalletSchema().update(item, new_item)
        else: # insert
            item = Wallet(**new_item)
        db.session.add(item)
        db.session.commit()
        return item


@blp.route('/<hostname>/<blockchain>')
class WalletsByHostname(MethodView):

    @blp.etag
    @blp.response(200, WalletSchema)
    def get(self, hostname, blockchain):
        return db.session.query(Wallet).filter(Wallet.hostname==hostname, Wallet.blockchain==blockchain).first()

    @blp.etag
    @blp.arguments(WalletSchema)
    @blp.response(200, WalletSchema)
    def put(self, new_item, hostname, blockchain):
        item = db.session.query(Wallet).filter(Wallet.hostname==hostname, Wallet.blockchain==blockchain)
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
    def delete(self, hostname, blockchain):
        item = db.session.query(Wallet).filter(Wallet.hostname==hostname, Wallet.blockchain==blockchain).first()
        blp.check_etag(item, WalletSchema)
        db.session.delete(item)
        db.session.commit()