from flask import Flask

app = Flask(__name__)
app.secret_key = b'$}#P)eu0A.O,s0Mz'

from app import routes
