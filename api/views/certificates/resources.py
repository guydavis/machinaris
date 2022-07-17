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

from common.config import globals
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
        if type == "stai":  # Due to renaming of blockchain
            blockchain = "staicoin"
        else:  # Use directly
            blockchain = type
        if not self.allow_download():
            abort(401) # Reject as not authorized
        zip = "/tmp/certs"
        zipname = "{0}.zip".format(zip)
        try:
            os.remove(zipname)
        except:
            pass
        dir = globals.get_blockchain_network_path(blockchain) + '/config/ssl/ca'
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
        return True