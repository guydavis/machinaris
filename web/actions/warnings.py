#
# Handle dismissable warnings to the user
#

import datetime
import json
import os
import re

from flask_babel import _, lazy_gettext as _l
from flask import flash, url_for
from configparser import ConfigParser

from common.models import warnings as w
from web import app, db, utils
from web.actions import worker

DISMISSED_SECTION = 'dismissed'
WARNINGS_PATH = '/root/.chia/machinaris/config/warnings.ini'

# Warning if the mnemonic file is still on disk after initial setup (key add)
def check_mnemonic_delete(msg):
    found_mnemonic = False
    try:
        for key_path in os.environ['keys'].split(':'):
            if os.path.exists(key_path):
                found_mnemonic = True
                app.logger.info("Found mnemonic key file at: {0}".format(key_path))
    except Exception as ex:
        app.logger.error("Failed to check for presence of mnemonic text files due to {0}".format(str(ex)))
    if found_mnemonic:
        flash(msg.format(url_for("index")), 'warning')
    return found_mnemonic

# Always recommend a cold wallet until they dismiss it
def check_cold_wallet(msg):
    flash(msg.format(url_for("index")), 'warning')
    return True

def load_warnings():
    try:
        config = ConfigParser()
        config.read(WARNINGS_PATH)
        return config
    except Exception as ex:
        app.logger.info("Unable to open warnings file at: {0}".format(WARNINGS_PATH))
    return None

def check_warnings(args):
    if not os.path.exists(WARNINGS_PATH):
        app.logger.info('Skipping warnings as no file found, so will now create one at: {0}'.format(WARNINGS_PATH))
        open(WARNINGS_PATH, 'a').close()  # Create empty file
        return # No warnings on very first Summary page load.

    config = load_warnings()

    # declare the warnings at runtime for translation
    WARNINGS = {
    'cold_wallet': [check_cold_wallet, \
            '<a class="btn btn-primary" style="float:right; margin-left:20px" role="button"href="{0}?cold_wallet=dismiss">' + _('Dismiss Warning') +'</a>' + \
                _("Machinaris uses an online wallet for farming. It is strongly recommended that you use a cold wallet for your payout instructions. Tutorial on the %(wiki_link_open)swiki%(wiki_link_close)s. Please add \"Setup a Cold Wallet\" to your To-Do list!", \
                    wiki_link_open='<a target="_blank" href="https://github.com/guydavis/machinaris/wiki/Keys#using-a-cold-wallet">', wiki_link_close='</a>')
        ],
    }

    # Now check if any warnings were dismissed by user
    updated = False
    for key in WARNINGS:
        if args.get(key) == "dismiss":
            if not config.has_section(DISMISSED_SECTION):
                config.add_section(DISMISSED_SECTION)
            config.set(DISMISSED_SECTION, key, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            updated = True
        elif config.has_option(DISMISSED_SECTION, key):
            app.logger.debug("Warning skipped as already dismissed by user: {0}".format(key))
        else:
            warning = WARNINGS[key]
            handler = warning[0]
            message = warning[1]
            handler(message)
    if updated:
        with open(WARNINGS_PATH, 'w') as f:
            config.write(f)

def get_plot_attrs(filename):
    dir,file = os.path.split(filename)
    match = re.match("plot(?:-mmx)?-k(\d+)-(\d+)-(\d+)-(\d+)-(\d+)-(\d+)-(\w+).plot", file)
    if match:
        short_plot_id = match.group(7)[:16]
        created_at = "{0}-{1}-{2} {3}:{4}".format( match.group(2),match.group(3),match.group(4),match.group(5),match.group(6))
    else:
        raise Exception("Malformed plot path/filename: {0}".format(filename))
    return [short_plot_id, dir, file, created_at]

def add_chia_plot_warning(result, hostname, blockchain, plot, created_at, updated_at):
    try:
        [short_plot_id, dir, file, plot_date] = get_plot_attrs(plot)
        warning_date = created_at
        if updated_at:
            warning_date = updated_at.strftime("%Y-%m-%d %H:%M:%S")
        result.append({
            'plot_id': short_plot_id,
            'hostname': hostname, 
            'worker': worker.get_worker(hostname).displayname,
            'blockchain': blockchain,
            'path': dir,
            'file': file,
            'reported_at': warning_date
        })
    except Exception as ex:
        app.logger.info(str(ex))

def load_plot_warnings():
    invalids = []
    missingkeys = []
    duplicates = []
    result = {}
    warnings = db.session.query(w.Warning).order_by(w.Warning.blockchain).all()
    for warning in warnings:
        if warning.type == 'missing_keys':
            for plot in json.loads(warning.content):
                add_chia_plot_warning(missingkeys, warning.hostname, warning.blockchain, plot, warning.created_at, warning.updated_at)
        elif warning.type == 'invalid_plots':
            for plot in json.loads(warning.content):
                add_chia_plot_warning(invalids, warning.hostname, warning.blockchain, plot, warning.created_at, warning.updated_at)
        elif warning.type == 'duplicate_plots':
            for plot in json.loads(warning.content):
                add_chia_plot_warning(duplicates, warning.hostname, warning.blockchain, plot, warning.created_at, warning.updated_at)
        elif warning.type == 'duplicated_plots_across_workers':
            dupes = json.loads(warning.content)
            for plot in dupes.keys():
                for dupe in dupes[plot]:
                    add_chia_plot_warning(duplicates, utils.convert_chia_ip_address(dupe['host']), warning.blockchain, dupe['path'] + '/' + plot, warning.created_at, warning.updated_at)
    result['duplicates'] = sorted(duplicates, key = lambda x: (x['plot_id'], x['worker'], x['path']))
    result['invalids'] = sorted(invalids, key = lambda x: (x['plot_id'], x['worker'], x['path']))
    result['missingkeys'] = sorted(missingkeys, key = lambda x: (x['plot_id'], x['worker'], x['path']))
    return result

def clear_plot_warnings():
    db.session.query(w.Warning).delete()
    db.session.commit()
    flash(_('Plot warnings have been cleared.  If they re-appear shortly, then please recheck the underlying cause has been addressed.'), 'success')
