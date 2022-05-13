import datetime as dt

from flask.views import MethodView

from api import app
from api.commands.smartctl import notify_failing_device
from api.extensions.api import Blueprint, SQLCursorPage
from common.extensions.database import db
from common.models import Drive
from api.commands import smartctl

from .schemas import DriveSchema, DriveQueryArgsSchema, BatchOfDriveSchema, BatchOfDriveQueryArgsSchema


blp = Blueprint(
    'Drive',
    __name__,
    url_prefix='/drives',
    description="Details on all drives recorded on the worker."
)


@blp.route('/')
class Drives(MethodView):

    @blp.etag
    @blp.arguments(BatchOfDriveQueryArgsSchema, location='query')
    @blp.response(200, DriveSchema(many=True))
    @blp.paginate(SQLCursorPage)
    def get(self, args):
        ret = db.session.query(Drive).filter_by(**args)
        return ret

    @blp.etag
    @blp.arguments(BatchOfDriveSchema)
    @blp.response(201, DriveSchema(many=True))
    def post(self, new_items):
        if len(new_items) == 0:
            return "No drives provided.", 400
        items = []
        for new_item in new_items:
            item = db.session.query(Drive).filter(Drive.hostname==new_item['hostname'], Drive.device==new_item['device']).first()
            if item: # upsert
                #app.logger.info("Upserting: {0} on {1}".format(new_item['device'], new_item['hostname']))
                new_item['created_at'] = item.created_at
                new_item['updated_at'] = dt.datetime.now()
                # Check for a status transition from PASSED to FAILED -> send an alert via Chiadog
                if item.status == 'PASSED' and 'status' in new_item and new_item['status'] != 'PASSED':
                    smartctl.notify_failing_device(new_item['hostname'], new_item['device'], new_item['status'])
                DriveSchema().update(item, new_item)
            else: # insert
                #app.logger.info("Inserting: {0} on {1}".format(new_item['device'], new_item['hostname']))
                new_item['created_at'] = new_item['updated_at'] = dt.datetime.now()
                # Check for a status of FAILED -> send an alert via Chiadog
                if 'status' in new_item and new_item['status'] != 'PASSED':
                    smartctl.notify_failing_device(new_item['hostname'], new_item['device'], new_item['status'])
                item = Drive(**new_item)
            db.session.add(item)
        db.session.commit()
        return items
