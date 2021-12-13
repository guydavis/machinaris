import asyncio
import datetime as dt
import json
import os
import traceback

from flask.views import MethodView

from api import app, utils
from api.extensions.api import Blueprint, SQLCursorPage
from common.extensions.database import db
from common.models import Plot
from common.models import workers as w

from .schemas import PlotSchema, PlotQueryArgsSchema, BatchOfPlotSchema, BatchOfPlotQueryArgsSchema

blp = Blueprint(
    'Plot',
    __name__,
    url_prefix='/plots',
    description="Operations on all plots on farmer"
)

# Holds the cached status of Plotman analyze and Chia plots check
STATUS_FILE = '/root/.chia/plotman/status.json'

def open_status_json():
    status = {}
    if os.path.exists(STATUS_FILE): 
        with open(STATUS_FILE, 'r+') as fp:
            status = json.load(fp)
    return status

def analyze_status(plots_status, short_plot_id):
    if short_plot_id in plots_status:
        if "analyze" in plots_status[short_plot_id]:
            if plots_status[short_plot_id]['analyze'] and 'seconds' in plots_status[short_plot_id]['analyze']:
                return plots_status[short_plot_id]['analyze']['seconds']
            else:
                return "-"
    return None

def check_status(plots_status, short_plot_id):
    if short_plot_id in plots_status:
        if "check" in plots_status[short_plot_id]:
            if plots_status[short_plot_id]['check'] and 'status' in plots_status[short_plot_id]['check']:
                return plots_status[short_plot_id]['check']['status']
            else:
                return "-"
    return None

def lookup_worker_displayname(displaynames, hostname):
    controller_hostname = utils.get_hostname()
    displaynames = {}
    if hostname in displaynames:
        displayname = displaynames[hostname]
    else: # Look up displayname
        try:
            # '172.18.0.1' was non-local IP on OlivierLA75's Docker setup, inside his container
            if hostname in ['127.0.0.1','172.18.0.1']:
                hostname = controller_hostname
            #app.logger.info("Found worker with hostname '{0}'".format(hostname))
            displayname = db.session.query(w.Worker).filter(w.Worker.hostname==hostname, 
                w.Worker.blockchain=='chia').first().displayname
        except:
            traceback.print_exc()
            app.logger.info("Unable to find a worker with hostname '{0}'".format(hostname))
            displayname = hostname
        displaynames[hostname] = displayname
    return displayname

@blp.route('/')
class Plots(MethodView):

    @blp.etag
    @blp.arguments(BatchOfPlotQueryArgsSchema, location='query')
    @blp.response(200, PlotSchema(many=True))
    @blp.paginate(SQLCursorPage)
    def get(self, args):
        ret = db.session.query(Plot).filter_by(**args)
        return ret

    @blp.etag
    @blp.arguments(BatchOfPlotSchema)
    @blp.response(201, PlotSchema(many=True))
    def post(self, new_items):
        # Re-enabled as Chives sends plots listing from its fullnode
        items = []
        displaynames = {}
        plots_status = open_status_json()
        for new_item in new_items:
            # Skip any previously sent by existing plot_id
            if not db.session.query(Plot).filter(Plot.hostname==new_item['hostname'], 
                Plot.plot_id==new_item['plot_id']).first():
                short_plot_id = new_item['plot_id'][:8]
                item = Plot(**new_item)
                item.displayname = lookup_worker_displayname(displaynames, new_item['hostname'])
                item.plot_analyze = analyze_status(plots_status, short_plot_id)
                item.plot_check = check_status(plots_status, short_plot_id)
                items.append(item)
                db.session.add(item)
        db.session.commit()
        return items

@blp.route('/<hostname>/<blockchain>')
class PlotByHostname(MethodView):

    @blp.etag
    @blp.response(200, PlotSchema)
    def get(self, hostname, blockchain):
        return db.session.query(Plot).filter(Plot.hostname==hostname, Plot.blockchain==blockchain)

    @blp.etag
    @blp.arguments(BatchOfPlotSchema)
    @blp.response(200, PlotSchema(many=True))
    def put(self, new_items, hostname, blockchain):
        # Re-enabled as Chives must send plots from each container
        items = []
        plots_status = open_status_json()
        for new_item in new_items:
            # Skip any previously sent by existing plot_id
            if not db.session.query(Plot).filter(Plot.hostname==new_item['hostname'], 
                Plot.plot_id==new_item['plot_id']).first():
                short_plot_id = new_item['plot_id'][:8]
                item = Plot(**new_item)
                item.plot_analyze = analyze_status(plots_status, short_plot_id)
                item.plot_check = check_status(plots_status, short_plot_id)
                items.append(item)
                db.session.add(item)
        db.session.commit()
        return items

    @blp.etag
    @blp.response(204)
    def delete(self, hostname, blockchain):
        db.session.query(Plot).filter(Plot.hostname==hostname, Plot.blockchain==blockchain).delete()
        db.session.commit()
