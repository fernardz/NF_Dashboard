from flask import render_template, flash, redirect, Blueprint, url_for, request, jsonify
from .models import Strava_Activity, Fitbit_Weight, Fitbit_Calories


stats_blueprint=Blueprint(
                'stats',
                __name__,
                template_folder='../templates/stats',
                url_prefix='/stats'
                )

@stats_blueprint.route('/')
@stats_blueprint.route('/index')
def index():
    weights=Fitbit_Weight.query.order_by(Fitbit_Weight.record_date.desc()).limit(3).all()
    activities=Strava_Activity.query.order_by(Strava_Activity.start_date_local.desc()).limit(3).all()
    calories=Fitbit_Calories.query.order_by(Fitbit_Calories.record_date.desc()).limit(3).all()
    return render_template('stats.html',title='Stats',
    weights=weights,
    activities=activities,
    calories=calories)

@stats_blueprint.route('/livefeed')
def lf():
    """Chat room. The user's name and room must be stored in
    the session."""
    return render_template('lf.html')
