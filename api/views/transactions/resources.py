import json
import os

from flask import request, make_response, abort
from flask.views import MethodView

from common.config import globals
from api import app
from api.commands import rpc
from api.extensions.api import Blueprint

blp = Blueprint(
    'Transaction',
    __name__,
    url_prefix='/transactions',
    description="Operations on transactions"
)

@blp.route('<id>')
class TransactionsByWalletId(MethodView):

    def get(self, id):
        blockchain_rpc = rpc.RPC()
        transactions = []
        if globals.enabled_blockchains()[0] != 'mmx':
            for t in blockchain_rpc.get_transactions(id, reverse=True):
                transactions.append(t.to_json_dict())
        response = make_response(json.dumps(transactions), 200)
        response.mimetype = "application/json"
        return response
