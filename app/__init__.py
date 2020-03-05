from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap
from flask_socketio import SocketIO

sql=SQLAlchemy()
socketio = SocketIO()


def create_app(object_name):
    app=Flask(__name__)
    app.config.from_object('config')
    sql.init_app(app)
    Bootstrap(app)

    from .stats import create_module as stats_create_module

    stats_create_module(app)

    socketio.init_app(app)
    return app
