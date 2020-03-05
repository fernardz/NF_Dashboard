from .models import db

def create_module(app, **kwargs):
    from .views import stats_blueprint
    app.register_blueprint(stats_blueprint)
