import json
import re
import traceback

from flask import request, make_response, abort
from flask.views import MethodView

from api import app
from api.extensions.api import Blueprint

blp = Blueprint(
    'Ping',
    __name__,
    url_prefix='/ping',
    description="Return an acknowledgement to test network access."
)


@blp.route('/')
class Logs(MethodView):

    def get(self):
        response = make_response(
            """Pong!
            """, 200)
        response.mimetype = "plain/text"
        return response

