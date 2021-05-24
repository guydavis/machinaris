
import pytz
import os
import time

from datetime import datetime
from flask import Flask, flash, redirect, render_template, request, session, url_for, send_from_directory

from app import app
from app.commands import global_config, chia_cli, plotman_cli, chiadog_cli, log_parser

@app.route('/')
def landing():
    gc = global_config.load()
    if not global_config.is_setup():
        return redirect(url_for('setup'))
    return render_template('landing.html')

@app.route('/index')
def index():
    gc = global_config.load()
    if not global_config.is_setup():
        return redirect(url_for('setup'))
    farming = chia_cli.load_farm_summary()
    plotting = plotman_cli.load_plotting_summary()
    challenges = log_parser.recent_challenges()
    return render_template('index.html', reload_seconds=60, 
        farming=farming.__dict__, plotting=plotting.__dict__, 
        challenges=challenges, global_config=gc)

@app.route('/setup', methods=['GET', 'POST'])
def setup():
    key_paths = global_config.get_key_paths()
    app.logger.info("Setup found these key paths: {0}".format(key_paths))
    show_setup = True
    if request.method == 'POST':
        show_setup = not chia_cli.generate_key(key_paths[0])
    if show_setup:
        return render_template('setup.html', key_paths = key_paths)
    else:
        return redirect(url_for('index'))

@app.route('/plotting', methods=['GET', 'POST'])
def plotting():
    gc = global_config.load()
    if request.method == 'POST':
        app.logger.info("Form submitted: {0}".format(request.form))
        if request.form.get('action') == 'start':
            plotman_cli.start_plotman()
        elif request.form.get('action') == 'stop':
            plotman_cli.stop_plotman()
        elif request.form.get('action') in ['suspend', 'resume', 'kill']:
            plotman_cli.action_plots(request.form)
        else:
            app.logger.info("Unknown plotting form: {0}".format(request.form))
    plotting = plotman_cli.load_plotting_summary()
    return render_template('plotting.html', reload_seconds=60,  plotting=plotting, 
        global_config=gc)

@app.route('/farming')
def farming():
    gc = global_config.load()
    farming = chia_cli.load_farm_summary()
    plots = chia_cli.load_plots_farming()
    chia_cli.compare_plot_counts(gc, farming, plots)
    return render_template('farming.html', farming=farming, plots=plots, 
        global_config=gc)

@app.route('/alerts', methods=['GET', 'POST'])
def alerts():
    gc = global_config.load()
    if request.method == 'POST':
        app.logger.info("Form submitted: {0}".format(request.form))
        if request.form.get('action') == 'start':
            chiadog_cli.start_chiadog()
        elif request.form.get('action') == 'stop':
            chiadog_cli.stop_chiadog()
        else:
            app.logger.info("Unknown alerts form: {0}".format(request.form))
    notifications = chiadog_cli.get_notifications()
    return render_template('alerts.html', chiadog_running = chiadog_cli.get_chiadog_pid(),
        reload_seconds=60, notifications=notifications, global_config=gc)

@app.route('/wallet')    
def wallet():
    gc = global_config.load()
    wallet = chia_cli.load_wallet_show()
    return render_template('wallet.html', wallet=wallet.text, 
        global_config=gc)

@app.route('/keys')
def keys():
    gc = global_config.load()
    keys = chia_cli.load_keys_show()
    key_paths = global_config.get_key_paths()
    return render_template('keys.html', keys=keys.text, 
        key_paths=key_paths, global_config=gc)

@app.route('/network/blockchain')
def network_blockchain():
    gc = global_config.load()
    blockchain = chia_cli.load_blockchain_show()
    return render_template('network/blockchain.html', reload_seconds=60, 
        blockchain=blockchain.text, global_config=gc, now=gc['now'])

@app.route('/network/connections', methods=['GET', 'POST'])
def network_connections():
    gc = global_config.load()
    if request.method == 'POST':
        if request.form.get('action') == "add":
            chia_cli.add_connection(request.form.get("connection"))
        else:
            app.logger.info("Unknown form action: {0}".format(request.form))
    connections = chia_cli.load_connections_show()
    return render_template('network/connections.html', reload_seconds=60, 
        connections=connections.text, global_config=gc, now=gc['now'])

@app.route('/settings/plotting', methods=['GET', 'POST'])
def settings_plotting():
    gc = global_config.load()
    if request.method == 'POST':
        config = request.form.get("plotman")
        plotman_cli.save_config(config)
    else: # Load config fresh from disk
        config = open('/root/.chia/plotman/plotman.yaml','r').read()
    return render_template('settings/plotting.html', config=config, 
        global_config=gc)

@app.route('/settings/farming', methods=['GET', 'POST'])
def settings_farming():
    gc = global_config.load()
    if request.method == 'POST':
        config = request.form.get("config")
        chia_cli.save_config(config)
    else: # Load config fresh from disk
        config = open('/root/.chia/mainnet/config/config.yaml','r').read()
    return render_template('settings/farming.html', config=config, 
        global_config=gc)

@app.route('/settings/alerts', methods=['GET', 'POST'])
def settings_alerts():
    gc = global_config.load()
    if request.method == 'POST':
        config = request.form.get("chiadog")
        chiadog_cli.save_config(config)
    else: # Load config fresh from disk
        config = open('/root/.chia/chiadog/config.yaml','r').read()
    return render_template('settings/alerts.html', config=config, 
        global_config=gc)

@app.route('/logs')
def logs():
    return render_template('logs.html')

@app.route('/logfile')
def logfile():
    log_file = None
    log_type = request.args.get("log")
    if log_type in [ 'alerts', 'farming', 'plotting']:
        return log_parser.get_log_lines(log_type)
    else:
        abort(500, "Unsupported log type: {0}".format(log_type))

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
            'favicon.ico', mimetype='image/vnd.microsoft.icon')