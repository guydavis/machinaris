from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()  # pylint: disable=invalid-name

def init_app(app):
    """Initialize relational database extension"""
    db.init_app(app)
    db.create_all(app=app)