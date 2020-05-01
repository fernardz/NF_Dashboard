from flask import session, current_app
import json
from flask_socketio import emit, join_room, leave_room
from datetime import datetime, timedelta
from .. import socketio, thread, thread_lock, create_app
from .models import Strava_Activity, Fitbit_Weight, Fitbit_Calories



def background_thread(app):
    count = 0
    with app.app_context():
        while True:
            socketio.sleep(30)
            count += 1
            today=datetime.today()
            last_week=datetime.today()-timedelta(days=7)
            last_week_str=last_week.strftime('%Y-%m-%d')
            weight=Fitbit_Weight.query\
            .filter(Fitbit_Weight.record_date>=last_week_str)\
            .order_by(Fitbit_Weight.record_date,Fitbit_Weight.record_time.desc())\
            .distinct(Fitbit_Weight.record_date).all()

            #activities=Strava_Activity.query.order_by(Strava_Activity.start_date_local.desc()).limit(10).all()
            activities=Strava_Activity.query\
            .filter(Strava_Activity.start_date_local>=last_week_str).all()

            calories=Fitbit_Calories.query.filter(Fitbit_Calories.record_date>=last_week_str)\
            .order_by(Fitbit_Calories.record_date.desc()).all()


            data_w=[d.as_json for d in weight]
            data_c=[d.as_json for d in calories]
            data_a=[d.as_json for d in activities]

            data={'weight':data_w,'calories':data_c,'activities':data_a}

            start=today-timedelta(days=today.weekday()+1)
            dates=[(start+timedelta(days=x)).strftime('%Y-%m-%d') for x in range(0,7)]
            socketio.emit('dates',
                        {'data':dates, 'today':today.strftime('%Y-%m-%d')}
                        ,namespace='/livefeed')
            #emit('stats_vals',{'data':data},namespace='/livefeed')
            socketio.sleep(3)
            socketio.emit('stats_vals',
                          {'data': data, 'count': count},
                          namespace='/livefeed')

@socketio.on('get_stats', namespace='/livefeed')
def stats(message):
    #weight=Fitbit_Weight.query.order_by(Fitbit_Weight.record_date.desc()).limit(10).all()
    today=datetime.today()
    last_week=datetime.today()-timedelta(days=7)
    last_week_str=last_week.strftime('%Y-%m-%d')
    weight=Fitbit_Weight.query\
    .filter(Fitbit_Weight.record_date>=last_week_str)\
    .order_by(Fitbit_Weight.record_date,Fitbit_Weight.record_time.desc())\
    .distinct(Fitbit_Weight.record_date).all()

    #activities=Strava_Activity.query.order_by(Strava_Activity.start_date_local.desc()).limit(10).all()
    activities=Strava_Activity.query\
    .filter(Strava_Activity.start_date_local>=last_week_str).all()

    calories=Fitbit_Calories.query.filter(Fitbit_Calories.record_date>=last_week_str)\
    .order_by(Fitbit_Calories.record_date.desc()).all()


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
    emit('dates',{'data':dates, 'today':today.strftime('%Y-%m-%d')},namespace='/livefeed')


@socketio.on('connect', namespace='/livefeed')
def test_connect():
    global thread
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(background_thread,(current_app._get_current_object()))
    emit('my_response', {'data': 'Connected2', 'count': 0})
