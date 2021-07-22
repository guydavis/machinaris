import json
import re
import traceback

from flask import request, make_response, abort
from flask.views import MethodView

from api import app
from api.extensions.api import Blueprint

from api.commands import chiadog_cli, chia_cli, plotman_cli

blp = Blueprint(
    'Config',
    __name__,
    url_prefix='/configs',
    description="Operations on all configs"
)


@blp.route('/')
class Configs(MethodView):

    def get(self):
        response = make_response(json.dumps(['alerts', 'farming', 'plotting']), 200)
        response.mimetype = "application/json"
        return response


@blp.route('/<type>')
class ConfigByType(MethodView):

    def get(self, type):
        if type == "plotting":
            config = plotman_cli.load_config()
        else: 
            try:
                blockchain = request.args.get('blockchain')
            except:
                abort(400, "Type of {0} request query parameter of blockchain=chia|flax.".format(type))
            if type == "farming":
                config = chia_cli.load_config(blockchain)
            elif type == "alerts":
                config = chiadog_cli.load_config(blockchain)
            else:
                abort(400, "Unknown config type provided: {0}".format(type))
        response = make_response(config, 200)
        response.mimetype = "application/x-yaml"
        return response

    def put(self, type):
        try:
            if type == "plotting":
                plotman_cli.save_config(self.clean_config(request.data))
            elif type in ["farming", "alerts"]:
                abort(400, "Farming and alerts config requires blockchain (chia or flax) in subpath.")
            else:
                abort(400, "Unknown config type provided: {0}".format(type))
            response = make_response("Successfully saved config.", 200)
            return response
        except Exception as ex:
            app.logger.info("Failed to save a validated Plotman config.")
            app.logger.info(traceback.format_exc())
            return str(ex), 400

    def clean_config(self, req_data):
        # First decode the bytes
        config = req_data.decode('utf-8')
        # Then strip off the leading and trailing double quote
        config = config[1:-1]
        # Now split lines correctly again
        config = config.replace('\\r\\n', '\r\n')
        return config

@blp.route('/<type>/<blockchain>')
class ConfigByType(MethodView):

    def put(self, type, blockchain):
        try:
            if type == "farming":
                chia_cli.save_config(self.clean_config(request.data), blockchain)
            elif type == "alerts":
                chiadog_cli.save_config(self.clean_config(request.data), blockchain)
            else:
                abort(400, "Unknown config type provided: {0}".format(type))
            response = make_response("Successfully saved config.", 200)
            return response
        except Exception as ex:
            app.logger.error(traceback.format_exc())
            abort(400, str(ex))

    def clean_config(self, req_data):
        # First decode the bytes
        config = req_data.decode('utf-8')
        # Then strip off the leading and trailing double quote
        config = config[1:-1]
        # Now split lines correctly again
        config = config.replace('\\r\\n', '\r\n')
        return config
