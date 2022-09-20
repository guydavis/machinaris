import json
import re
import time
import traceback

from flask import request, make_response, abort
from flask.views import MethodView

from api import app
from api.extensions.api import Blueprint

from api.commands import chiadog_cli, chia_cli, plotman_cli, pools_cli
from api.schedules import status_worker, status_plotting, status_farm, \
    status_alerts, status_connections, status_pools, status_plotnfts

blp = Blueprint(
    'Action',
    __name__,
    url_prefix='/actions',
    description="Actions to take"
)

@blp.route('/')
class Actions(MethodView):

    def post(self):
        app.logger.info("Received /actions request with {0}".format(request.data))
        try:
            body = json.loads(request.data)
            service = body['service']
        except:
            abort("Invalid action request without service.", 400)
        try:
            if service in ["plotting", "archiving"]:
                plotman_cli.dispatch_action(body)
                msg = "Plotman action completed."
            elif service in [ "farming", "networking", "wallet" ]:
                chia_cli.dispatch_action(body)
                msg = "Blockchain action completed."
            elif service == "monitoring":
                chiadog_cli.dispatch_action(body)
                msg = "Chiadog action completed."
            elif service == "pooling":
                msg = pools_cli.dispatch_action(body)
            else:
                abort("Unknown service provided: {0}".format(service))
            # Now trigger updates after a delay
            time.sleep(17)
            status_worker.update()
            if service in ["plotting", "archiving"]:
                status_plotting.update()
            elif service == "farming":
                status_farm.update()
            elif service == "networking":
                status_connections.update()
            elif service == "monitoring":
                status_alerts.update()
            elif service == "pooling":
                status_plotnfts.update()
                status_pools.update()
            time.sleep(3) # Time for status update to reach database
            return make_response(msg, 200)
        except Exception as ex:
            app.logger.error(traceback.format_exc())
            return str(ex), 400
