import pytz
import os

from datetime import datetime
from flask import render_template, redirect, url_for

from app import app
from app.commands import chia_cli, plotman_cli

@app.route('/')
def index():
    if not chia_cli.is_setup():
        return redirect(url_for('setup'))
    farming = chia_cli.load_farm_summary()
    plotting = plotman_cli.load_plotting_summary()
    now = datetime.now(tz=None)
    return render_template('index.html', reload_seconds=30, now=now,
        farming=farming.__dict__, plotting=plotting.__dict__)

@app.route('/setup')
def setup():
    return render_template('setup.html')

@app.route('/plotting')
def plotting():
    plotting = plotman_cli.load_plotting_summary()
    now = datetime.now(tz=None)
    return render_template('plotting.html', reload_seconds=30, now=now, 
        columns=plotting.columns, rows=plotting.rows)

@app.route('/settings/plotting')
def settings_plotting():
    return render_template('settings/plotting.html')

@app.route('/settings/farming')
def settings_farming():
    return render_template('settings/farming.html')

@app.route('/settings/alerts')
def settings_alerts():
    return render_template('settings/alerts.html')

@app.route('/settings/keys')    
def settings_keys():
    return render_template('settings/keys.html')
