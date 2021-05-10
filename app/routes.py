from flask import render_template
from app import app

@app.route('/')
def index():
    user = {'username': 'Guy'}
    return render_template('index.html', title="Machinaris", user=user)


@app.route('/setup')
def setup():
    return render_template('setup.html')