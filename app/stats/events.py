from flask import session
import json
from flask_socketio import emit, join_room, leave_room
from datetime import datetime, timedelta
from .. import socketio, thread, thread_lock
from .models import Strava_Activity, Fitbit_Weight, Fitbit_Calories

@socketio.on('joined', namespace='/livefeed')
def joined(message):
    """Sent by clients when they enter a room.
    A status message is broadcast to all people in the room."""
    emit('status has entered the room.')


@socketio.on('get_stats', namespace='/livefeed')
def stats(message):
    weight=Fitbit_Weight.query.order_by(Fitbit_Weight.record_date.desc()).limit(3).all()
    activities=Strava_Activity.query.order_by(Strava_Activity.start_date_local.desc()).limit(3).all()
    calories=Fitbit_Calories.query.order_by(Fitbit_Calories.record_date.desc()).limit(3).all()
    data_w=[d.as_json for d in weight]
    data_c=[d.as_json for d in calories]
    data_a=[d.as_json for d in activities]

    data={'weight':data_w,'calories':data_c,'activities':data_a}

    emit('stats_vals',{'data':data},namespace='/livefeed')

@socketio.on('get_week', namespace='/livefeed')
def stats(message):
    today=datetime.today()
    start=today-timedelta(days=today.weekday()+1)
    dates=[(start+timedelta(days=x)).strftime('%Y-%m-%d') for x in range(0,7)]
    emit('dates',{'data':dates},namespace='/livefeed')


@socketio.on('left', namespace='/livefeed')
def left(message):
    print('Client disconnected')
