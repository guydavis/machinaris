import datetime as dt

from flask.views import MethodView

from api import app
from api.extensions.api import Blueprint, SQLCursorPage
from common.extensions.database import db
from common.models import Alert

from .schemas import AlertSchema, AlertQueryArgsSchema, BatchOfAlertSchema, BatchOfAlertQueryArgsSchema


blp = Blueprint(
    'Alert',
    __name__,
    url_prefix='/alerts',
    description="Operations on all alerts on farmer"
)


@blp.route('/')
class Alerts(MethodView):

    @blp.etag
    @blp.arguments(BatchOfAlertQueryArgsSchema, location='query')
    @blp.response(200, AlertSchema(many=True))
    @blp.paginate(SQLCursorPage)
    def get(self, args):
        ret = Alert.query.filter_by(**args)
        return ret

    @blp.etag
    @blp.arguments(BatchOfAlertSchema)
    @blp.response(201, AlertSchema(many=True))
    def post(self, new_items):
        items = []
        for new_item in new_items:
            item = db.session.query(Alert).get(new_item['unique_id'])
            if not item:  # Request contains previously received alerts, only add new
                item = Alert(**new_item)
                items.append(item)
                db.session.add(item)
        db.session.commit()
        return items


@blp.route('/<hostname>/<blockchain>')
class AlertByHostnameBlockchain(MethodView):

    @blp.etag
    @blp.response(200, AlertSchema)
    def get(self, hostname, blockchain):
        return db.session.query(Alert).filter(Alert.hostname==hostname, Alert.blockchain==blockchain)

    @blp.etag
    @blp.arguments(BatchOfAlertSchema)
    @blp.response(200, AlertSchema(many=True))
    def put(self, new_items, hostname, blockchain):
        items = []
        for new_item in new_items:
            item = db.session.query(Alert).get(new_item['unique_id'])
            if not item:  # Request contains previously received alerts, only add new
                item = Alert(**new_item)
                items.append(item)
                db.session.add(item)
        db.session.commit()
        return items

    @blp.etag
    @blp.response(204)
    def delete(self, hostname, blockchain):
        db.session.query(Alert).filter(Alert.hostname==hostname, Alert.blockchain==blockchain).delete()
        db.session.commit()
