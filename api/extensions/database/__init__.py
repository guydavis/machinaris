"""Relational database"""

from flask_sqlalchemy import SQLAlchemy

#from sqlalchemy.ext.compiler import compiles
#from sqlalchemy.sql import Insert

db = SQLAlchemy()  # pylint: disable=invalid-name

#Insert.argument_for('sqlite', 'on_conflict_do_nothing', False)

#@compiles(Insert, 'sqlite')
#def suffix_insert(insert, compiler, **kwargs):
#    stmt = compiler.visit_insert(insert, **kwargs)
#    if insert.dialect_kwargs.get('sqlite_on_conflict_do_nothing'):
#        stmt += ' ON CONFLICT DO NOTHING'
#    return stmt

def init_app(app):
    """Initialize relational database extension"""
    db.init_app(app)
    db.create_all(app=app)