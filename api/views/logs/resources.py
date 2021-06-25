import json
import re
import traceback

from flask import request, make_response, abort
from flask.views import MethodView

from api import app
from api.extensions.api import Blueprint

from api.commands import log_parser

blp = Blueprint(
    'Log',
    __name__,
    url_prefix='/logs',
    description="Operations on all logs"
)


@blp.route('/')
class Logs(MethodView):

    def get(self):
        response = make_response(json.dumps(['alerts', 'farming', 'plotting', 'archiving']), 200)
        response.mimetype = "application/json"
        return response


@blp.route('/<type>')
class LogByType(MethodView):

    def get(self, type):
        log = log_parser.get_log_lines(type, request.args.get('log_id'))
        response = make_response(log, 200)
        response.mimetype = "plain/text"
        return response
