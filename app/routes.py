import pytz
import os

from datetime import datetime, timezone
from flask import render_template

from app import app
from app.commands import chia_cli, plotman_cli

@app.route('/')
def index():
    farming = chia_cli.load_farm_summary()
    plotting = plotman_cli.load_plotting_summary()
    now = datetime.now(timezone.utc).astimezone(pytz.timezone(os.environ['TZ'])).strftime("%Y-%m-%d %H:%M:%S")
    #app.logger.info('%s', summary.__dict__)
    return render_template('index.html', reload_seconds=30, now=now, title="Machinaris", 
        farming=farming.__dict__, plotting=plotting.__dict__)

@app.route('/setup')
def setup():
    return render_template('setup.html')