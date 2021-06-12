import datetime as dt

from flask.views import MethodView

from api import app
from api.extensions.api import Blueprint, SQLCursorPage
from common.extensions.database import db
from common.models import Connection

from .schemas import ConnectionSchema, ConnectionQueryArgsSchema


blp = Blueprint(
    'Connections',
    __name__,
    url_prefix='/connections',
    description="Operations on connections"
)


@blp.route('/')
class Connections(MethodView):

    @blp.etag
    @blp.arguments(ConnectionQueryArgsSchema, location='query')
    @blp.response(200, ConnectionSchema(many=True))
    @blp.paginate(SQLCursorPage)
    def get(self, args):
        return Connection.query.filter_by(**args)

    @blp.etag
    @blp.arguments(ConnectionSchema)
    @blp.response(201, ConnectionSchema)
    def post(self, new_item):
        item = Connection.query.get(new_item['hostname'])
        if item: # upsert
            new_item['created_at'] = item.created_at
            new_item['updated_at'] = dt.datetime.now()
            ConnectionSchema().update(item, new_item)
        else: # insert
            item = Connection(**new_item)
        db.session.add(item)
        db.session.commit()
        return item


@blp.route('/<hostname>')
class ConnectionsByHostname(MethodView):

    @blp.etag
    @blp.response(200, ConnectionSchema)
    def get(self, hostname):
        return Connection.query.get_or_404(hostname)

    @blp.etag
    @blp.arguments(ConnectionSchema)
    @blp.response(200, ConnectionSchema)
    def put(self, new_item, hostname):
        item = Connection.query.get_or_404(hostname)
        new_item['hostname'] = item.hostname
        new_item['created_at'] = item.created_at
        new_item['updated_at'] = dt.datetime.now()
        blp.check_etag(item, ConnectionSchema)
        ConnectionSchema().update(item, new_item)
        db.session.add(item)
        db.session.commit()
        return item

    @blp.etag
    @blp.response(204)
    def delete(self, hostname):
        item = Connection.query.get_or_404(hostname)
        blp.check_etag(item, ConnectionSchema)
        db.session.delete(item)
        db.session.commit()