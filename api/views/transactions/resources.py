import json
import re
import traceback

from flask import request, make_response, abort
from flask.views import MethodView

from api import app
from api.extensions.api import Blueprint

from api.rpc import chia

blp = Blueprint(
    'Transaction',
    __name__,
    url_prefix='/transactions',
    description="Operations on transactions"
)

@blp.route('<id>')
class LogByType(MethodView):

    def get(self, id):
        transactions = []
        for t in chia.get_transactions(id, reverse=True):
            transactions.append(t.to_json_dict())
        response = make_response(json.dumps(transactions), 200)
        response.mimetype = "application/json"
        return response
