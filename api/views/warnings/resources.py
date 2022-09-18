import datetime as dt
import traceback

from flask.views import MethodView

from api import app
from api.commands.websvcs import cold_wallet_balance
from api.extensions.api import Blueprint, SQLCursorPage
from api.commands import websvcs
from common.extensions.database import db
from common.models import Warning

from .schemas import WarningSchema, WarningQueryArgsSchema, BatchOfWarningSchema, BatchOfWarningQueryArgsSchema


blp = Blueprint(
    'Warnings',
    __name__,
    url_prefix='/warnings',
    description="Operations on warnings"
)

@blp.route('/<hostname>/<blockchain>/<type>')
class WarningsByHostname(MethodView):

    @blp.etag
    @blp.arguments(BatchOfWarningSchema)
    @blp.response(200, WarningSchema(many=True))
    def post(self, new_items, hostname, blockchain, type):
        items = []
        for new_item in new_items:
            item = db.session.query(Warning).filter(
                Warning.hostname==hostname, 
                Warning.blockchain==blockchain,  
                Warning.type==type).first()
            if item:
                #app.logger.info("Updating for {0}/{1}/{2}".format(hostname, blockchain, type))
                new_item['created_at'] = item.created_at
                new_item['updated_at'] = dt.datetime.now()
                new_item['title'] = item.title
                new_item['service'] = item.service
                new_item['content'] = item.content
                WarningSchema().update(item, new_item)
            else:
                #app.logger.info("Inserting for {0}/{1}/{2}".format(hostname, blockchain, type))
                item = Warning(**new_item)
            items.append(item)
            db.session.add(item)
            db.session.commit()
        return items

    @blp.etag
    @blp.response(204)
    def delete(self, hostname, blockchain, type):
        db.session.query(Warning).filter( \
            Warning.hostname==hostname, 
            Warning.blockchain==blockchain,  
            Warning.type==type).delete()
        db.session.commit()