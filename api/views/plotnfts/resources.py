import datetime as dt
import http
import json
import requests
import threading

from flask.views import MethodView

from api import app
from api.extensions.api import Blueprint, SQLCursorPage
from common.extensions.database import db
from common.models import Plotnft, Worker

from .schemas import PlotnftSchema, BatchOfPlotnftSchema

blp = Blueprint(
    'Plotnfts',
    __name__,
    url_prefix='/plotnfts',
    description="Operations on plotnfts"
)

@blp.route('/')
class Plotnfts(MethodView):

    @blp.arguments(BatchOfPlotnftSchema)
    @blp.response(201, PlotnftSchema(many=True))
    def post(self, new_items):
        plotnfts = []
        items = []
        for new_item in new_items:
            item = db.session.query(Plotnft).filter(Plotnft.unique_id==new_item['unique_id']).first()            
            if item:
                new_item['created_at'] = item.created_at
                new_item['updated_at'] = dt.datetime.now()
                PlotnftSchema().update(item, new_item)
            else:
                item = Plotnft(**new_item)
            db.session.add(item)
            plotnfts.append({
                'unique_id': item.unique_id,
                'hostname': item.hostname,
                'blockchain': item.blockchain,
                'launcher': item.launcher,
                'pool_contract_address': item.pool_contract_address(),
                'wallet_num': item.wallet_num,
                'header': item.header,
                'details': item.details,
                'created_at': item.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                'updated_at': item.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
            })
            items.append(item)
        db.session.commit()
        # Whenever the Chia plotnfts are updated, share info with other blockchain fullnodes for NFT 7/8 reward recovery later
        if len(plotnfts) > 0 and plotnfts[0]['blockchain'] == 'chia':
            from chia.util.byte_types import hexstr_to_bytes
            from chia.util.bech32m import decode_puzzle_hash
            from chia.types.blockchain_format.sized_bytes import bytes32
            for plotnft in plotnfts:
                puzzle_bytes = decode_puzzle_hash(plotnft['pool_contract_address'])
                plotnft['puzzle_hash'] = puzzle_bytes.hex()
                for wk in db.session.query(Worker).filter(Worker.mode=='fullnode', Worker.blockchain!='chia').all():
                    if wk.connection_status() == 'Responding':
                        thread = threading.Thread(target=self.save_chia_plotnft_config,
                            kwargs={
                                'url': wk.url + '/configs/plotnfts/' + wk.blockchain,
                                'plotnfts': plotnfts,
                                'debug': False
                            }
                        )
                        thread.start()
        return items

    def save_chia_plotnft_config(self, url, plotnfts, debug):
        headers = {'Content-type': 'application/json', 'Accept': 'application/json'}
        if debug:
            http.client.HTTPConnection.debuglevel = 1
        response = requests.put(url, headers = headers, data = json.dumps(plotnfts))
        http.client.HTTPConnection.debuglevel = 0
        return response

@blp.route('/<hostname>/<blockchain>')
class PlotNftByHostname(MethodView):

    @blp.etag
    @blp.response(200, PlotnftSchema)
    def get(self, hostname, blockchain):
        return db.session.query(Plotnft).filter(Plotnft.hostname==hostname, Plotnft.blockchain==blockchain)

    @blp.etag
    @blp.response(204)
    def delete(self, hostname, blockchain):
        db.session.query(Plotnft).filter(Plotnft.hostname==hostname, Plotnft.blockchain==blockchain).delete()
        db.session.commit()
