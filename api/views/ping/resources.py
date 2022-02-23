import json
import re
import traceback

from flask import request, make_response, abort
from flask.views import MethodView
from flask_babel import _, lazy_gettext as _l

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
        app.logger.info("IN PING, MATCH IS {0}".format(request.accept_languages.best_match(app.config['LANGUAGES'])))
        app.logger.info("IN PING, PONG IS {0}".format(_('Pong!')))
        response = make_response(
            """{0}
""".format(_('Pong!')), 200)
        response.mimetype = "plain/text"
        return response

