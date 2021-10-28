import json
import re
import time
import threading
import traceback

from flask import request, make_response, abort
from flask.views import MethodView

from api import app
from api.extensions.api import Blueprint

from api.commands import fd_cli

blp = Blueprint(
    'Reward',
    __name__,
    url_prefix='/rewards',
    description="Rewards to recover on forks"
)

@blp.route('/')
class Rewards(MethodView):

    def post(self):
        try:
            body = json.loads(request.data)
            blockchain = body['blockchain']
            wallet_id = body['wallet_id']
            launcher_id = body['launcher_id']
            pool_contract_address = body['pool_contract_address']
        except:
            abort("Invalid rewards recovery request without blockchain, launcher_id, or pool_contract_address.", 400)
        
        if blockchain in ['chia', 'chives']:
            abort(f"No need to recover rewards for blockchain: {blockchain}")

        try:
            thread = threading.Thread(target=fd_cli.reward_recovery, 
                kwargs={
                    'wallet_id': wallet_id, 
                    'launcher_id': launcher_id, 
                    'pool_contract_address': pool_contract_address
                }
            )
            thread.start()
            return make_response("Recovery started.", 200)
        except Exception as ex:
            app.logger.info(traceback.format_exc())
            return str(ex), 400
