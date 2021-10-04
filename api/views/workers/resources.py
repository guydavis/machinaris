import datetime as dt
import pytz
import os

from flask import request, make_response, abort
from flask.views import MethodView

from api import app
from api.extensions.api import Blueprint, SQLCursorPage
from common.extensions.database import db
from common.models import Worker

from .schemas import WorkerSchema, WorkerQueryArgsSchema


blp = Blueprint(
    'Workers',
    __name__,
    url_prefix='/workers',
    description="Operations on workers"
)


@blp.route('/')
class Workers(MethodView):

    @blp.etag
    @blp.arguments(WorkerQueryArgsSchema, location='query')
    @blp.response(200, WorkerSchema(many=True))
    @blp.paginate(SQLCursorPage)
    def get(self, args):
        return db.session.query(Worker).filter_by(**args)

@blp.route('/<hostname>/<port>')
class WorkersByHostname(MethodView):

    @blp.etag
    @blp.arguments(WorkerSchema)
    @blp.response(200, WorkerSchema)
    def post(self, new_item, hostname, port):
        item = db.session.query(Worker).filter(Worker.hostname==hostname, Worker.port==port).first()
        if item: # update
            new_item['created_at'] = item.created_at
            new_item['updated_at'] = dt.datetime.now()
            new_item['latest_ping_result'] = item.latest_ping_result
            new_item['ping_success_at'] = item.ping_success_at
            WorkerSchema().update(item, new_item)
        else: # insert
            item = Worker(**new_item)
        db.session.add(item)
        db.session.commit()
        return item

    @blp.etag
    @blp.response(204)
    def delete(self, hostname, port):
        item = db.session.query(Worker).filter(Worker.hostname==hostname, Worker.port==port).first()
        if item:
            blp.check_etag(item, WorkerSchema)
            db.session.delete(item)
            db.session.commit()
