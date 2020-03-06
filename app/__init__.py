from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap
from flask_socketio import SocketIO
from threading import Lock

sql=SQLAlchemy()
socketio = SocketIO(async_mode = None)


thread = None
thread_lock = Lock()

def create_app(object_name):
    app=Flask(__name__)
    app.config.from_object('config')
    sql.init_app(app)
    Bootstrap(app)

    from .stats import create_module as stats_create_module



    socketio.init_app(app)
    stats_create_module(app)

    return app
