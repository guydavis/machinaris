import os

from datetime import datetime
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, DateTime, ForeignKey

from api import app

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////root/.chia/chiadog/dbs/chiadog.db'
db = SQLAlchemy(app)

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    priority = db.Column(db.String(40), nullable=False)
    service = db.Column(db.String(60), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)

    def __repr__(self):
        return '{0} {1}-{2}: {3}'.format(self.created_at, self.priority, self.service, self.message)
