import json
import re
import traceback

from flask import request, make_response, abort
from flask.views import MethodView

from api import app
from api.extensions.api import Blueprint
from api.commands import plotman_cli

blp = Blueprint(
    'Metrics',
    __name__,
    url_prefix='/metrics',
    description="Return plotman prometheus metrics"
)


@blp.route('/')
class Logs(MethodView):

    def get(self):
      metrics = plotman_cli.get_prometheus_metrics()
      if metrics:
        response = make_response(metrics, 200)
        response.mimetype = "plain/text"
        return response
      else:
        return make_response("Sorry, something went wrong...", 404)

