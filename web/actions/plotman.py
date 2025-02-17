#
# CLI interactions with the plotman script.
#

import datetime
import json
import os
import psutil
import re
import signal
import shutil
import time
import traceback
import yaml

from flask import Flask, jsonify, abort, request, flash
from flask.helpers import make_response
from flask_babel import _, lazy_gettext as _l
from subprocess import Popen, TimeoutExpired, PIPE

from common.models import plottings as pl, transfers as t, keys as k
from web import app, db, utils
from web.models.plotman import PlottingSummary, ArchivingSummary
from . import worker as w
from . import pools as p

PLOTMAN_SCRIPT = '/chia-blockchain/venv/bin/plotman'
REPLOTTING_CONFIG = '/root/.chia/machinaris/config/replotting.json'

# Don't query plotman unless at least this long since last time.
RELOAD_MINIMUM_SECS = 30

def load_plotting_summary(hostname=None):
    query = db.session.query(pl.Plotting)
    if hostname:
        plottings = query.filter(pl.Plotting.hostname==hostname)
    else:
        plottings = query.all()
    return PlottingSummary(plottings)

def load_plotting_summary_by_blockchains(blockchains):
    summary = {}
    for blockchain in blockchains:
        summary[blockchain] = _('Idle') # Default, unless a job found
    for plotting in db.session.query(pl.Plotting).all():
        if plotting.stat != 'STP':
            summary[plotting.blockchain] = _('Active')
        elif plotting.stat == 'STP' and summary[plotting.blockchain] != _('Active'):
            summary[plotting.blockchain] = _('Suspended')
    if 'chia' in summary and summary['chia']:
        for blockchain in blockchains: # All forks sharing Chia plots show as "Active" too
            if not blockchain in pl.PLOTTABLE_BLOCKCHAINS:
                summary[blockchain] = summary['chia']
    #app.logger.info(summary)
    return summary

def load_archiving_summary(hostname=None):
    query = db.session.query(t.Transfer)
    if hostname:
        transfers = query.filter(t.Transfer.hostname==hostname)
    else:
        transfers = query.all()
    return ArchivingSummary(transfers)

def load_plotters():
    return w.load_worker_summary().plotters()

def start_plotman(plotter):
    app.logger.info("Starting Plotman run...")
    try:
        response = utils.send_post(plotter, "/actions/", {"service": "plotting","action": "start"}, debug=False)
    except:
        app.logger.info(traceback.format_exc())
        flash(_('Failed to start Plotman plotting run! Please see log files.'), 'danger')
    else:
        if response.status_code == 200:
            flash(_('Plotman started successfully.'), 'success')
        else:
            flash("<pre>{0}</pre>".format(response.content.decode('utf-8')), 'danger')

def action_plots(action, plot_ids):
    plots_by_worker = group_plots_by_worker(plot_ids)
    app.logger.info("About to {0} plots: {1}".format(action, plots_by_worker))
    error = False
    error_message = ""
    for hostname_blockchain in plots_by_worker.keys():
        try:
            [ hostname, blockchain] = hostname_blockchain.split('_')
            plotter = w.get_worker(hostname, blockchain)
            plot_ids = plots_by_worker[hostname_blockchain]
            response = utils.send_post(plotter, "/actions/", debug=False,
                payload={"service": "plotting","action": action, "plot_ids": plot_ids}
            )
            if response.status_code != 200:
                error_message += response.content.decode('utf-8') + "\n"
        except:
            error = True
            app.logger.info(traceback.format_exc())
    if error:
        flash(_('Failed to %(action)s all plots!', action=action), 'danger')
        flash('<pre>{0}</pre>'.format(error_message), 'warning')
    else:
        flash(_('Plotman was able to %(action)s the selected plots successfully.', action=action), 'success')

def group_plots_by_worker(plot_ids):
    plots_by_worker = {}
    all_plottings = load_plotting_summary()
    for plot_id in plot_ids:
        hostname_blockchain = None
        for plot in all_plottings.rows:
            if plot['plot_id'] == plot_id:
                hostname_blockchain = plot['hostname'] + '_' + plot['fork']
        if hostname_blockchain:
            if not hostname_blockchain in plots_by_worker:
                plots_by_worker[hostname_blockchain] = []
            plots_by_worker[hostname_blockchain].append(plot_id)
    return plots_by_worker

def stop_plotman(plotter):
    app.logger.info("Stopping Plotman run...")
    try:
        response = utils.send_post(plotter, "/actions/", payload={"service": "plotting","action": "stop"}, debug=False)
    except:
        app.logger.info(traceback.format_exc())
        flash(_('Failed to stop Plotman plotting run!'), 'danger')
        flash('Please see /root/.chia/plotman/logs/plotman.log', 'warning')
    else:
        if response.status_code == 200:
            flash(_('Plotman stopped successfully. No new plots will be started, but existing ones will continue on.'), 'success')
        else:
            flash("<pre>{0}</pre>".format(response.content.decode('utf-8')), 'danger')

def start_archiving(plotter):
    app.logger.info("Starting Archiver....")
    try:
        response = utils.send_post(plotter, "/actions/", {"service": "archiving","action": "start"}, debug=False)
    except:
        app.logger.info(traceback.format_exc())
        flash(_('Failed to start Plotman archiver! Please see log files.'), 'danger')
    else:
        if response.status_code == 200:
            flash(_('Archiver started successfully.'), 'success')
        else:
            flash("<pre>{0}</pre>".format(response.content.decode('utf-8')), 'danger')

def stop_archiving(plotter):
    app.logger.info("Stopping Archiver run....")
    try:
        response = utils.send_post(plotter, "/actions/", payload={"service": "archiving","action": "stop"}, debug=False)
    except:
        app.logger.info(traceback.format_exc())
        flash(_('Failed to stop Plotman archiver. Please see:') + ' /root/.chia/plotman/logs/archiver.log', 'danger')
    else:
        if response.status_code == 200:
            flash(_('Archiver stopped successfully.'), 'success')
        else:
            flash("<pre>{0}</pre>".format(response.content.decode('utf-8')), 'danger')

def load_key_pk(type, blockchain):
    try:
        #app.logger.info("Searching for {0} replacement in {1}".format(type, blockchain))
        key = db.session.query(k.Key).filter(k.Key.blockchain==blockchain).first()
        #app.logger.info(key.details)
        m = re.search(r'{0} public key.*:\s+(\w+)'.format(type.lower()), key.details.lower())
        if m:
            #app.logger.info("Found: {0}".format(m.group(1)))
            return m.group(1)
    except Exception as ex:
        app.logger.info("Failed to extract {0} key for {1} because {2}.".format(type, blockchain, ))
    return None

def load_pool_contract_address(blockchain):
    pool_blockchain = blockchain
    plotnfts = p.load_plotnfts_by_blockchain(pool_blockchain)
    if len(plotnfts.rows) == 1:
        m = re.search(r'Pool contract address .*: (\w+)'.format(type), plotnfts.rows[0]['details'])
        if m:
            return m.group(1)
    elif len(plotnfts.rows) > 1:
        app.logger.info("Did not find a unique Pool contract address as multiple plotnfts exist. Not replacing in plotman.yaml.")
    return None

def load_config_replacements(blockchain):
    replacements = []
    farmer_pk = load_key_pk('Farmer', blockchain)
    if farmer_pk:
        #app.logger.info("FARMER_PK: {0}".format(farmer_pk))
        replacements.append([ r'farmer_pk:\s+REPLACE_WITH_THE_REAL_VALUE.*$', 'farmer_pk: '+ farmer_pk ])
    pool_pk = load_key_pk('Pool', blockchain)
    if pool_pk:
        #app.logger.info("POOL_PK: {0}".format(pool_pk))
        replacements.append([ r'pool_pk:\s+REPLACE_WITH_THE_REAL_VALUE.*$', 'pool_pk: '+ pool_pk])
    pool_contract_address = load_pool_contract_address(blockchain)
    if pool_contract_address:
        #app.logger.info("POOL_CONTRACT_ADDRESS: {0}".format(pool_contract_address))
        replacements.append([ r'pool_contract_address:\s+REPLACE_WITH_THE_REAL_VALUE.*$', 'pool_contract_address: '+ pool_contract_address])
    return replacements

def load_config(plotter, blockchain):
    replacements = []
    try:
        replacements = load_config_replacements(blockchain)
    except:
        app.logger.info("Unable to load replacements on install with mode={0}".format(os.environ['mode']))
        app.logger.info(traceback.format_exc())
    lines = []
    config = utils.send_get(plotter, "/configs/plotting/" + blockchain, debug=False).content.decode('utf-8')
    replaces = 0
    for line in config.splitlines():
        for replacement in replacements:
            (line, num_replaces) = re.subn(replacement[0], replacement[1], line)
            replaces += num_replaces
        lines.append(line)
    if replaces > 0:
        #app.logger.info("Return true for replaced.")
        return [ True, '\n'.join(lines) ]
    else:
        #app.logger.info("Return false for replaced.")
        return [ False, '\n'.join(lines) ]

def load_dirs(plotter, blockchain):
    result = utils.send_get(plotter, "/configs/plotting_dirs/" + blockchain, debug=False).content.decode('utf-8')
    return result

def inspect_config(hostname, config):
    if 'plotting' in config:
        if 'pool_contract_address' in config['plotting']:
            app.logger.info("Saving config to {0}, found pool_contract_address {1}".format(
                hostname, config['plotting']['pool_contract_address']))
        elif 'pool_pk' in config['plotting']:
            app.logger.info("Saving config to {0}, found pool_pk {1}".format(
                hostname, config['plotting']['pool_pk']))
            flash(_('Current configuration will plot %(open_b)sSOLO%(close_b)s plots, not %(open_b)sPORTABLE%(close_b)s plots for pooling. If this is not your choice, please see the %(wiki_open)swiki%(wiki_close)s.', 
                open_b='<b>', close_b='</b>', wiki_open='<a target="_blank" href="https://github.com/guydavis/machinaris/wiki/Pooling#setup-and-config">', wiki_close='</a>'), 'message')
    else:
         app.logger.info("Saving config to {0}, found a malformed config without a 'plotting' section.")

def save_config(plotter, blockchain, config):
    try: # Validate the YAML first
        c = yaml.safe_load(config)
        inspect_config(plotter.hostname, c)
    except Exception as ex:
        app.logger.info(traceback.format_exc())
        flash(_('Updated plotman.yaml failed validation! Fix and save or refresh page.'), 'danger')
        flash(str(ex), 'warning')
    try:
        response = utils.send_put(plotter, "/configs/plotting/" + blockchain, config, debug=False)
    except Exception as ex:
        flash(_('Failed to save config to plotter. Please check log files.'), 'danger')
        flash(str(ex), 'warning')
    else:
        if response.status_code == 200:
            flash(_('Nice! Plotman\'s plotman.yaml validated and saved successfully.'), 'success')
        else:
            flash("<pre>{0}</pre>".format(response.content.decode('utf-8')), 'danger')

def analyze(plot_id):
    analyze_file = '/root/.chia/plotman/analyze/{0}.log'.format(plot_id)
    app.logger.info("Analyze request for {0}".format(analyze_file))
    if os.path.exists(analyze_file):
        with open(analyze_file, 'r+') as fp:
            return fp.read()
    return make_response(_("Sorry, no plotting job log found. Perhaps plot was made outside Machinaris?"), 200)

def load_plotting_keys(blockchain):
    farmer_pk = load_key_pk('Farmer', blockchain)
    pool_pk = load_key_pk('Pool', blockchain)
    pool_contract_address = load_pool_contract_address(blockchain)
    if not farmer_pk:
        farmer_pk = None if os.environ['farmer_pk'] == 'null' else os.environ['farmer_pk']
    if not pool_pk:
        pool_pk = None if os.environ['pool_pk'] == 'null' else os.environ['pool_pk']
    if not pool_contract_address:
        pool_contract_address = None if os.environ['pool_contract_address'] == 'null' else os.environ['pool_contract_address']
    return [farmer_pk, pool_pk, pool_contract_address]

def load_replotting_settings():
    settings = {}
    if os.path.exists(REPLOTTING_CONFIG):
        with open(REPLOTTING_CONFIG, 'r') as fp:
            settings = json.loads(fp.read())
    for blockchain in pl.PLOTTABLE_BLOCKCHAINS:
        if not blockchain in settings:  # Default is to have replotting disabled.
            settings[blockchain] = { "enabled": False, "delete_solo": False, "delete_uncompressed": False, "free_ksize": 32, }
    return settings

def save_replotting_settings(form):
    settings = load_replotting_settings()
    app.logger.info(form)
    replotting_enabled = []
    for blockchain in pl.PLOTTABLE_BLOCKCHAINS:
        settings[blockchain]['enabled'] = form.get('replotting_{0}'.format(blockchain)) == 'true'
        if settings[blockchain]['enabled']:
            replotting_enabled.append(blockchain.capitalize())
        settings[blockchain]['free_ksize'] = int(form.get('replotting_{0}_free_ksize'.format(blockchain)))
        settings[blockchain]['delete_solo'] = form.get('replotting_{0}_delete_solo'.format(blockchain)) == 'true'
        settings[blockchain]['delete_uncompressed'] = form.get('replotting_{0}_delete_uncompressed'.format(blockchain)) == 'true'
        settings[blockchain]['delete_before'] = form.get('replotting_{0}_delete_before'.format(blockchain)) == 'true'
        settings[blockchain]['delete_before_date'] = form.get('replotting_{0}_delete_before_date'.format(blockchain))
        settings[blockchain]['delete_by_ksize'] = form.get('replotting_{0}_delete_by_ksize'.format(blockchain)) == 'true'
        settings[blockchain]['delete_by_ksizes'] = list(map(int, form.getlist('replotting_{0}_delete_by_ksizes'.format(blockchain))))
    try:
        with open(REPLOTTING_CONFIG, 'w') as f:
            json.dump(settings, f)
        if replotting_enabled:
            flash(_('Replotting has been enabled for %(blockchains)s. Please start Plotting (and Archiving) once free space for replotting appears in about 15 minutes.', blockchains=', '.join(replotting_enabled)), 'success')
        else:
            flash(_('Replotting has been DISABLED for all blockchains.  Machinaris will NOT remove any plots now.'), 'success')
    except Exception as ex:
        msg = _("Unable to save replotting settings in %(file)s because %(exception)s", file=REPLOTTING_CONFIG, exception=str(ex))
        app.logger.error(msg)
        flash(msg, 'danger')
        return
    return settings


def load_schedule(plotter, blockchain):
    result = utils.send_get(plotter, "/configs/plotting_schedule/" + blockchain, debug=False).content.decode('utf-8')
    return json.loads(result)

# Method is invoked by a XHR post from the Settings | Plotting page.  Don't use flash()
def save_schedules(worker, blockchain, schedule):
    try:
        response = utils.send_put(worker, "/configs/plotting_schedule/" + blockchain, schedule, debug=False)
    except Exception as ex:
        app.logger.error('Failed to save schedule to plotter because {0}'.format(str(ex)))
    else:
        app.logger.info('Plotting schedule has been saved and applied.  Current plotting manager status of running or stopped is not immediately affected.')
