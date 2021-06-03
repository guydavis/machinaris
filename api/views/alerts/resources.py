import datetime as dt

from flask.views import MethodView

from api import app
from api.extensions.api import Blueprint, SQLCursorPage
from common.extensions.database import db
from common.models import Alert

from .schemas import AlertSchema, AlertQueryArgsSchema


blp = Blueprint(
    'Alert',
    __name__,
    url_prefix='/alerts',
    description="Ops for alerts"
)


@blp.route('/')
class Alerts(MethodView):

    @blp.etag
    @blp.arguments(AlertQueryArgsSchema, location='query')
    @blp.response(200, AlertSchema(many=True))
    @blp.paginate(SQLCursorPage)
    def get(self, args):
        return Alert.query.filter_by(**args)

    @blp.etag
    @blp.arguments(AlertSchema)
    @blp.response(201, AlertSchema)
    def post(self, new_item):
        item = Alert(**new_item)
        db.session.add(item)
        db.session.commit()
        return item


@blp.route('/<id>')
class AlertsById(MethodView):

    @blp.etag
    @blp.response(200, AlertSchema)
    def get(self, id):
        return Alert.query.get_or_404(id)

    @blp.etag
    @blp.arguments(AlertSchema)
    @blp.response(200, AlertSchema)
    def put(self, new_item, id):
        app.logger.info("new_item: {0}".format(new_item))
        item = Alert.query.get_or_404(id)
        new_item['created_at'] = item.created_at
        new_item['updated_at'] = dt.datetime.now()
        blp.check_etag(item, AlertSchema)
        AlertSchema().update(item, new_item)
        db.session.add(item)
        db.session.commit()
        return item

    @blp.etag
    @blp.response(204)
    def delete(self, id):
        item = Alert.query.get_or_404(id)
        blp.check_etag(item, AlertSchema)
        db.session.delete(item)
        db.session.commit()
