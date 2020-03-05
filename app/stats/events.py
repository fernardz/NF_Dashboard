from flask import session
import json
from flask_socketio import emit, join_room, leave_room
from .. import socketio
from .models import Strava_Activity, Fitbit_Weight, Fitbit_Calories


@socketio.on('joined', namespace='/livefeed')
def joined(message):
    """Sent by clients when they enter a room.
    A status message is broadcast to all people in the room."""
    emit('status has entered the room.')


@socketio.on('weight', namespace='/livefeed')
def weight(message):
    """Sent by a client when the user entered a new message.
    The message is sent to all people in the room."""
    weight=Fitbit_Weight.query.order_by(Fitbit_Weight.record_date.desc()).limit(3).all()
    data=json.dumps([d.as_json for d in weight], default=str)
    emit('weight_vals',{'data':data},namespace='/livefeed')


@socketio.on('left', namespace='/livefeed')
def left(message):
    print('Client disconnected')
