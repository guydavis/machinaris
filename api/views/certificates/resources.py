import datetime
import json
import os
import re
import shutil
import time
import traceback

from flask import request, Response, abort
from flask.views import MethodView

from api import app
from api.extensions.api import Blueprint

from api.commands import chia_cli, plotman_cli

blp = Blueprint(
    'Certificates',
    __name__,
    url_prefix='/certificates',
    description="Certificates to perform"
)


@blp.route('/')
class Certificates(MethodView):

    def get(self):
        type = request.args.get('type')
        if type == "btcgreen":
            blockchain = "btcgreen"
            dir = "/root/.btcgreen/mainnet/config/ssl/ca"
        elif type == "cactus":
            blockchain = "cactus"
            dir = "/root/.cactus/mainnet/config/ssl/ca"
        elif type == "chia":
            blockchain = "chia"
            dir = "/root/.chia/mainnet/config/ssl/ca"
        elif type == "chives":
            blockchain = "chives"
            dir = "/root/.chives/mainnet/config/ssl/ca"
        elif type == "cryptodoge":
            blockchain = "cryptodoge"
            dir = "/root/.cryptodoge/mainnet/config/ssl/ca"
        elif type == "flax":
            blockchain = "flax"
            dir = "/root/.flax/mainnet/config/ssl/ca"
        elif type == "flora":
            blockchain = "flora"
            dir = "/root/.flora/mainnet/config/ssl/ca"
        elif type == "nchain":
            blockchain = "nchain"
            dir = "/root/.chia/ext9/config/ssl/ca"
        elif type == "hddcoin":
            blockchain = "hddcoin"
            dir = "/root/.hddcoin/mainnet/config/ssl/ca"
        elif type == "maize":
            blockchain = "maize"
            dir = "/root/.maize/mainnet/config/ssl/ca"
        elif type == "silicoin":
            blockchain = "silicoin"
            dir = "/root/.silicoin/mainnet/config/ssl/ca"
        elif type == "shibgreen":
            blockchain = "shibgreen"
            dir = "/root/.shibgreen/mainnet/config/ssl/ca"
        elif type == "staicoin":
            blockchain = "staicoin"
            dir = "/root/.staicoin/mainnet/config/ssl/ca"
        elif type == "stor":
            blockchain = "stor"
            dir = "/root/.stor/mainnet/config/ssl/ca"
        else:
            abort(400) # Bad blockchain type passed
        if blockchain == 'chia' and not self.allow_download():
            abort(401) # Reject as not authorized
        zip = "/tmp/certs".format(blockchain)
        zipname = "{0}.zip".format(zip)
        try:
            os.remove(zipname)
        except:
            pass
        shutil.make_archive(zip, 'zip', dir)
        with open(zipname, 'rb') as f:
            data = f.readlines()
            os.remove(zipname)
        return Response(data, headers={
            'Content-Type': 'application/zip',
            'Content-Disposition': 'attachment; filename=certs.zip;'
        })

    def allow_download(self):
        allow_harvester_cert_lan_download = app.config['ALLOW_HARVESTER_CERT_LAN_DOWNLOAD']
        if not allow_harvester_cert_lan_download: # Override if set in configuration file
            app.logger.info("Harvester cert download over LAN disallowed as per api.cfg.")
            return False
        worker_setup_marker = "/root/.chia/machinaris/tmp/worker_launch.tmp"
        if os.path.exists(worker_setup_marker):
            last_modified_date = datetime.datetime.fromtimestamp(os.path.getmtime(worker_setup_marker))
            fifteen_minutes_ago = datetime.datetime.now() - datetime.timedelta(minutes=30)
            if last_modified_date >= fifteen_minutes_ago:
                return True
            app.logger.info("Harvester cert download over LAN disallowed due to timeout guard on New Worker page launch.")
        return False