import datetime as dt

from flask.views import MethodView

from api import app
from api.extensions.api import Blueprint, SQLCursorPage
from common.extensions.database import db
from common.models import Challenge

from .schemas import ChallengeSchema, ChallengeQueryArgsSchema, BatchOfChallengeSchema, BatchOfChallengeQueryArgsSchema


blp = Blueprint(
    'Challenge',
    __name__,
    url_prefix='/challenges',
    description="Operations on all challenges recorded on farmer"
)


@blp.route('/')
class Challenges(MethodView):

    @blp.etag
    @blp.arguments(BatchOfChallengeQueryArgsSchema, location='query')
    @blp.response(200, ChallengeSchema(many=True))
    @blp.paginate(SQLCursorPage)
    def get(self, args):
        ret = db.session.query(Challenge).filter_by(**args)
        return ret

    @blp.etag
    @blp.arguments(BatchOfChallengeSchema)
    @blp.response(201, ChallengeSchema(many=True))
    def post(self, new_items):
        if len(new_items) == 0:
            return "No challenges provided.", 400
        items = []
        for new_item in new_items:
            item = db.session.query(Challenge).get(new_item['unique_id'])
            if not item:  # Request contains previously received challenges, only add new
                item = Challenge(**new_item)
                items.append(item)
                db.session.add(item)
        db.session.commit()
        return items


@blp.route('/<hostname>/<blockchain>')
class ChallengeByHostname(MethodView):

    @blp.etag
    @blp.response(200, ChallengeSchema)
    def get(self, hostname, blockchain):
        return db.session.query(Challenge).filter(Challenge.hostname==hostname, Challenge.blockchain==blockchain)

    @blp.etag
    @blp.arguments(BatchOfChallengeSchema)
    @blp.response(200, ChallengeSchema(many=True))
    def put(self, new_items, hostname, blockchain):
        items = []
        for new_item in new_items:
            item = db.session.query(Challenge).get(new_item['unique_id'])
            if not item:  # Request contains previously received challenges, only add new
                item = Challenge(**new_item)
                items.append(item)
                db.session.add(item)
        db.session.commit()
        return items

    @blp.etag
    @blp.response(204)
    def delete(self, hostname, blockchain):
        db.session.query(Challenge).filter(Challenge.hostname==hostname, Challenge.blockchain==blockchain).delete()
        db.session.commit()
