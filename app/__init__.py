from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap
from flask_socketio import SocketIO
from flask_migrate import Migrate
from threading import Lock

db=SQLAlchemy()
socketio = SocketIO(async_mode = 'eventlet')
thread = None
thread_lock = Lock()
migrate = Migrate()

def create_app(object_name):
    app=Flask(__name__)
    app.config.from_object(object_name)
    db.init_app(app)
    migrate.init_app(app, db)
    Bootstrap(app)

    from .stats import create_module as stats_create_module


    stats_create_module(app)
    socketio.init_app(app)


    return app
