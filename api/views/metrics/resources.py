import json
import re
import traceback

from flask import request, make_response, abort
from flask.views import MethodView

from common.config import globals

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
class Metrics(MethodView):

    def get(self):
      return make_response("Invalid metrics type requested.  Please request /metrics/prometheus endpoint.", 400)
    

@blp.route('/<type>')
class MetricsByType(MethodView):

    def get(self, type):
      if type != 'prometheus':
        return make_response("Invalid metrics type requested.  Please request /metrics/prometheus endpoint.", 400)

      if globals.plotting_enabled():
        metrics = plotman_cli.get_prometheus_metrics()
        if metrics:
          response = make_response(metrics, 200)
          response.mimetype = "plain/text"
          return response
        else:
          return make_response("Failed to retrieve plotman metrics.", 500)
      else:
        return make_response("Plotting not enabled on this Machinaris worker.", 404)
