import os

from datetime import datetime
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, DateTime, ForeignKey, func

from common.extensions.database import db

from api import app

class Notification(db.Model):
    __bind_key__ = 'chiadog'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    priority = db.Column(db.String(40), nullable=False)
    service = db.Column(db.String(60), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, server_default=func.now(), nullable=False)
