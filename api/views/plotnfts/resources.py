import datetime as dt

from flask.views import MethodView

from api import app
from api.extensions.api import Blueprint, SQLCursorPage
from common.extensions.database import db
from common.models import Plotnft

from .schemas import PlotnftSchema, PlotnftQueryArgsSchema

from api.commands import chia_cli

blp = Blueprint(
    'Plotnfts',
    __name__,
    url_prefix='/plotnfts',
    description="Operations on plotnfts"
)


@blp.route('/')
class Plotnfts(MethodView):

    @blp.etag
    @blp.arguments(PlotnftQueryArgsSchema, location='query')
    @blp.response(200, PlotnftSchema(many=True))
    @blp.paginate(SQLCursorPage)
    def get(self, args):
        # Trigger an update when receieved from web-tier immediately after create/join/leave
        chia_cli.load_plotnft_show('chia')
        return db.session.query(Plotnft).filter_by(**args)

    @blp.etag
    @blp.arguments(PlotnftSchema)
    @blp.response(201, PlotnftSchema)
    def post(self, new_item):
        item = db.session.query(Plotnft).filter(Plotnft.hostname==new_item['hostname'], \
            Plotnft.blockchain==new_item['blockchain']).first()
        if item: # upsert
            new_item['created_at'] = item.created_at
            new_item['updated_at'] = dt.datetime.now()
            PlotnftSchema().update(item, new_item)
        else: # insert
            item = Plotnft(**new_item)
        db.session.add(item)
        db.session.commit()
        return item


@blp.route('/<hostname>/<blockchain>')
class PlotnftsByHostname(MethodView):

    @blp.etag
    @blp.response(200, PlotnftSchema)
    def get(self, hostname, blockchain):
        return db.session.query(Plotnft).get_or_404(hostname)

    @blp.etag
    @blp.arguments(PlotnftSchema)
    @blp.response(200, PlotnftSchema)
    def put(self, new_item, hostname, blockchain):
        item = db.session.query(Plotnft).filter(Plotnft.hostname==hostname, Plotnft.blockchain==blockchain)
        new_item['hostname'] = item.hostname
        new_item['created_at'] = item.created_at
        new_item['updated_at'] = dt.datetime.now()
        blp.check_etag(item, PlotnftSchema)
        PlotnftSchema().update(item, new_item)
        db.session.add(item)
        db.session.commit()
        return item

    @blp.etag
    @blp.response(204)
    def delete(self, hostname):
        item = db.session.query(Plotnft).get_or_404(hostname)
        blp.check_etag(item, PlotnftSchema)
        db.session.delete(item)
        db.session.commit()