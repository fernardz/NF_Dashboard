from .models import db

def create_module(app, **kwargs):
    from .views import stats_blueprint
    from . import events
    app.register_blueprint(stats_blueprint)
