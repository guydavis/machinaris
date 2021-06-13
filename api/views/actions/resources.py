import json
import re
import time
import traceback

from flask import request, make_response, abort
from flask.views import MethodView

from api import app
from api.extensions.api import Blueprint

from api.commands import chiadog_cli, chia_cli, plotman_cli
from api.schedules import status_worker, status_plotting, status_farm, status_alerts

blp = Blueprint(
    'Action',
    __name__,
    url_prefix='/actions',
    description="Actions to take"
)

@blp.route('/')
class Actions(MethodView):

    def post(self):
        try:
            body = json.loads(request.data)
            service = body['service']
        except:
            abort("Invalid action request without service.", 400)
        try:
            if service == "plotting":
                plotman_cli.dispatch_action(body)
                time.sleep(5)
                status_plotting.update()
            elif service == "farming":
                chia_cli.dispatch_action(body)
                time.sleep(5)
                status_farm.update()
                status_plots.update()
            elif service == "monitoring":
                chiadog_cli.dispatch_action(body)
                time.sleep(5)
                status_alerts.update()
            else:
                abort("Unknown service provided: {0}".format(service))
            status_worker.update()  # Always update worker status
            return make_response("Action completed.", 200)
        except Exception as ex:
            app.logger.info(traceback.format_exc())
            abort("Failed during {0} action.".format(service), 500)
