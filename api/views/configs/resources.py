import json
import re
import traceback

from flask import request, make_response, abort
from flask.views import MethodView

from api import app
from api.extensions.api import Blueprint

from api.commands import chiadog_cli, chia_cli, plotman_cli, forktools_cli, mmx_cli, rewards

blp = Blueprint(
    'Config',
    __name__,
    url_prefix='/configs',
    description="Operations on all configs"
)


@blp.route('/')
class Configs(MethodView):

    def get(self):
        response = make_response(json.dumps(['alerts', 'farming', 'plotting', 'forktools']), 200)
        response.mimetype = "application/json"
        return response

@blp.route('/<type>/<blockchain>')
class ConfigByType(MethodView):

    def get(self, type, blockchain):
        mimetype = "application/x-yaml"
        if type == "farming":
            if blockchain == 'mmx':
                config = mmx_cli.load_config(blockchain)
            else:
                config = chia_cli.load_config(blockchain)
        elif type == "alerts":
            config = chiadog_cli.load_config(blockchain)
        elif type == "plotting":
            config = plotman_cli.load_config(blockchain)
        elif type == "plotting_dirs":
            config = plotman_cli.load_dirs(blockchain)
            mimetype = "application/json"
        elif type == "tools":
            config = forktools_cli.load_config(blockchain)
        else:
            abort(400, "Unknown config type provided: {0}".format(type))
        response = make_response(config, 200)
        response.mimetype = mimetype
        return response

    def clean_config(self, req_data):
        # First decode the bytes
        config = req_data.decode('utf-8')
        # Then strip off the leading and trailing double quote
        config = config[1:-1]
        # Then deal with any escaped double quotes within the config
        config = config.replace('\\"', '"')
        # Now split lines correctly again
        config = config.replace('\\r\\n', '\n')
        return config

    def put(self, type, blockchain):
        try:
            if type == "farming":
                chia_cli.save_config(self.clean_config(request.data), blockchain)
            elif type == "alerts":
                chiadog_cli.save_config(self.clean_config(request.data), blockchain)
            elif type == "plotting":
                plotman_cli.save_config(self.clean_config(request.data), blockchain)
            elif type == "tools":
                forktools_cli.save_config(self.clean_config(request.data), blockchain)
            elif type == "wallet":
                chia_cli.save_wallet_settings(json.loads(request.data.decode('utf-8')), blockchain)
            elif type == "plotnfts":
                rewards.save_chia_plotnfts(json.loads(request.data.decode('utf-8')))
            else:
                abort(400, "Unknown config type provided: {0}".format(type))
            response = make_response("Successfully saved config.", 200)
        except Exception as ex:
            app.logger.error("Error attempting to save {0} config: ".format(type))
            app.logger.error(traceback.format_exc())
            human_readable_error = str(ex)
            response = make_response(human_readable_error, 400)
        return response
