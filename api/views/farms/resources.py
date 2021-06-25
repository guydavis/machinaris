import datetime as dt

from flask.views import MethodView

from api import app
from api.extensions.api import Blueprint, SQLCursorPage
from common.extensions.database import db
from common.models import Farm

from .schemas import FarmSchema, FarmQueryArgsSchema


blp = Blueprint(
    'Farm',
    __name__,
    url_prefix='/farms',
    description="Ops for farms"
)


@blp.route('/')
class Farms(MethodView):

    @blp.etag
    @blp.arguments(FarmQueryArgsSchema, location='query')
    @blp.response(200, FarmSchema(many=True))
    @blp.paginate(SQLCursorPage)
    def get(self, args):
        return Farm.query.filter_by(**args)

    @blp.etag
    @blp.arguments(FarmSchema)
    @blp.response(201, FarmSchema)
    def post(self, new_item):
        item = Farm.query.get(new_item['hostname'])
        if item: # upsert
            new_item['created_at'] = item.created_at
            new_item['updated_at'] = dt.datetime.now()
            FarmSchema().update(item, new_item)
        else: # insert
            item = Farm(**new_item)
        db.session.add(item)
        db.session.commit()
        return item


@blp.route('/<hostname>')
class FarmsByHostname(MethodView):

    @blp.etag
    @blp.response(200, FarmSchema)
    def get(self, hostname):
        return Farm.query.get_or_404(hostname)

    @blp.etag
    @blp.arguments(FarmSchema)
    @blp.response(200, FarmSchema)
    def put(self, new_item, hostname):
        item = Farm.query.get_or_404(hostname)
        new_item['hostname'] = item.hostname
        new_item['created_at'] = item.created_at
        new_item['updated_at'] = dt.datetime.now()
        blp.check_etag(item, FarmSchema)
        FarmSchema().update(item, new_item)
        db.session.add(item)
        db.session.commit()
        return item

    @blp.etag
    @blp.response(204)
    def delete(self, hostname):
        item = Farm.query.get_or_404(hostname)
        blp.check_etag(item, FarmSchema)
        db.session.delete(item)
        db.session.commit()
