# Building a Fitness Tracking Dashboard with Python. Pt 3 Flask and Deployment

Now that we have a way to store our information in a database and reliably access the API's that contain our information we need to provide a way to deploy it and also a nice enough looking interface.
For deployment like every other project made in the last 3 years we will spin up a docker container with all our services to make housekeeping easy. For the frontend (and some additional other services) we will use a Flask Application with socketio to pass the information to the client.

## Project Organization
In the previous post I explained the setup for a project, however some additional changes are made to make it easy to deploy our project.
The structure now looks like this:
```
\app
  \static
    \examples
    \js
  \stats
    __init__.py
    models.py
    events.py
    views.py
  \templates
  	\stats
    	lf.html
    base.html
  __init__.py
\creds
	creds.txt
  creds_fitbit.txt
\migrations
config.py
docker-compose.yml
docker-entrypoint.sh
Dockerfile_server
Dockerfile_updater
requirements.txt
requirements_updater.txt
run.py
stats_con.py
tasks.py
wsgi.py
```
Overall the main changes are the creation of a views.py to handle our pages. events.py which provides our socketio implementation.
We also create a migrations folder to take to use with alembic and flask for database migrations.
Finally we also create all our docker files and our gunicorn wsgi file to handle our web server.

## Flask Application

Since we want to be able to view and update our data easily we roll out a Flask tap and take advantage of its myriad of available plugins, mainly Flask-Migrate, Flask-Socketio, Flask-Bootstrap and Flask-SQLAlchemy (as was mentioned in the previous post).
Since we need to initialize all these modules our app level __app\\\_\_init\_\_.py__ is modified to the following.
```Python
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
```

In the previous post we were using `Base=declarative_base()` however since we are now using Flask-SqlAlchemy we are going to be inheriting from `db.Model` instead so our class is modified to the to do so. We also add an `as_json` property to each to allow control over our models json representation.
```Python
from .. import db

class Strava_Activity(db.Model):
    __tablename__='strava_activity'
    #index=db.Column(Integer(), primary_key=True)
    id=db.Column(db.BigInteger(), primary_key=True)
    owner=db.Column(db.Integer())#Probs Foregin keyring
    activity_type=db.Column(db.String(50))
    distance=db.Column(db.Float())
    elapsed_time=db.Column(db.Float())
    average_speed=db.Column(db.Float())
    average_cadence=db.Column(db.Float())
    average_heartrate=db.Column(db.Float())
    name=db.Column(db.String(50))
    utc_offset=db.Column(db.Float())
    max_speed=db.Column(db.Float())
    max_heartrate=db.Column(db.Float())
    total_elevation_gain=db.Column(db.Float())
    upload_id=db.Column(db.BigInteger())
    moving_time=db.Column(db.Float())
    start_date=db.Column(db.DateTime())
    start_date_local=db.Column(db.DateTime())
    last_time = db.Column(db.TIMESTAMP, server_default=db.func.now(), onupdate=db.func.current_timestamp())

    @property
    def as_json(self):
       #Return object data in easily serializable format
       return {
    'index':self.id,
    'speed':self.average_speed,
    'cadence':self.average_cadence,
    'heartrate':self.average_heartrate,
    'distance':self.distance,
    'moving_time':self.moving_time,
    'date':self.start_date_local.strftime('%Y-%m-%d')}

    def __repr__(self):
        return "<STRAVA ACTIVITY '%s', distance='%s', type='%s', date='%s'>"%(self.id, self.distance, self.activity_type, self.start_date_local)

class Fitbit_Weight(db.Model):
    __tablename__='fitbit_weight'
    id=db.Column(db.BigInteger(), primary_key=True)
    weight=db.Column(db.Float(), nullable=False)
    bmi=db.Column(db.Float())
    fat=db.Column(db.Float())
    record_date=db.Column(db.DateTime())
    record_time=db.Column(db.Time())
    last_time = db.Column(db.TIMESTAMP, server_default=db.func.now(), onupdate=db.func.current_timestamp())
    @property
    def as_json(self):
       #Return object data in easily serializable format
       return {
    'index':self.id,
    'weight':self.weight,
    'fat':self.fat,
    'bmi':self.bmi,
    'date':self.record_date.strftime('%Y-%m-%d')}

    def __repr__(self):
        return "<FITBIT WEIGHT '%s', weight='%s', bmi='%s', date='%s'>"%(self.id, self.weight, self.bmi, self.record_date)



class Fitbit_Calories(db.Model):
    __tablename__='fitbit_calories'
    id=db.Column(db.BigInteger(), primary_key=True)
    calories=db.Column(db.Float())
    record_date=db.Column(db.DateTime())
    last_time = db.Column(db.TIMESTAMP, server_default=db.func.now(), onupdate=db.func.current_timestamp())

    @property
    def as_json(self):
       #Return object data in easily serializable format
       return {
    'index':self.id,
    'calories':self.calories,
    'date':self.record_date.strftime('%Y-%m-%d')}

    def __repr__(self):
        return "<FITBIT Calories '%s', calories='%s', date='%s'>"%(self.id, self.calories, self.record_date)
```

Following that we are initializing socketio and defining the async mode to use eventlet. We also have some threading parameters to allow us to change that behavior and have control over our background process and initialize Flask-Migrate to take care of the migrations.
Our `create_app()` method takes care of initializing our application factory. We use a configuration object to pass all our parameters for the application.
`Bootstrap(app)` allows us to have a nice interface without doing much.
The last step is to initialize our socketio using socketio.init_app

### Retrieving Data using Socketio
Since we want to be able to update the client without user input we are going to be periodically pushing out  the most current information in the database.
We could whip up some jquery client side to push for data however in situation I do not want pass requests to the server and will just publish to a common room allow multiple clients to connect and receive the data.
In order to do so we create a background thread in charge of pushing out the updated data. This defined in __events.py__
```Python
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

    today=datetime.today()
    last_week=datetime.today()-timedelta(days=7)
    last_week_str=last_week.strftime('%Y-%m-%d')
    weight=Fitbit_Weight.query\
    .filter(Fitbit_Weight.record_date>=last_week_str)\
    .order_by(Fitbit_Weight.record_date,Fitbit_Weight.record_time.desc())\
    .distinct(Fitbit_Weight.record_date).all()

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

```
The background_thread(app) will be doing the bulk of the work. Here we are passing our app instance to a separate thread and tasking it with querying the database and emitting the data back to our clients. This will emit every 33 seconds due to the 2 socketio.sleep() instructions.

In order to do so we need to use with app.app_context(): to make sure that the we can access the correct socket.io and have visibility to our app.
To retrieve the data from the postgres database we use Flask-Alchemy for example to retrieve the weight information we use the following code:

This query retrieves the weight information for the current week and orders the in descending order .
After we retrieve all the information we need to pass we store the json into an array inside a dictionary as follows.

This data can then be emitted to a specific group (or namespace), in our case the __livefeed__ namespace.

Again all of this is wrapped with app.app_context() so it can interact with our application instance.

The `get_week()` and `get_stats()` events are convenience methods for debugging and to demand updated data from the client side.

Finally the `test_connect()` method makes sure that if the background thread is alive.

### Flask View Configuration
Our webapp will be pretty simple one route will display the last 3 records in each of our tables and another one will display the self updating week view. We will use flask blueprints to accomplish this.

```Python
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
    return render_template('lf.html')
```

The _index_ route just queries our tables to return the information. We then pass those values to the _jinja_ template.

```html
{% extends "base.html" %}
{% block content %}
<div class="row title_block_center"><h1>Stats</h1></div>
<div class="row title_block_center"><h4>Strava</h4></div>
  <table class="table">
     <thead>
       <tr>
         <th>Date</th>
         <th>Distance</th>
         <th>Time</th>
       </tr>
     </thead>
     <tbody>
       {% for act in activities %}

       <tr>
         <td>{{act.start_date_local}}</td>
         <td> {{"%.2f"| format(act.distance * 0.000621371)}}</td>
         <td>{{"%.2f" | format(act.moving_time/60)}}</td>
       </tr>
       {% endfor %}
   </tbody>
 </table>

 <div class="row title_block_center"><h4>Weight</h4></div>
   <table class="table">
      <thead>
        <tr>
          <th>Date</th>
          <th>Time</th>
          <th>Weight</th>
        </tr>
      </thead>
      <tbody>
        {% for weight in weights %}

        <tr>
          <td>{{weight.record_date}}</td>
          <td> {{weight.record_time}}</td>
          <td>{{weight.weight}}</td>
        </tr>
        {% endfor %}
    </tbody>
  </table>

  <div class="row title_block_center"><h4>Calories</h4></div>
    <table class="table">
       <thead>
         <tr>
           <th>Date</th>
           <th>Calories</th>
         </tr>
       </thead>
       <tbody>
         {% for cal in calories %}

         <tr>
           <td>{{cal.record_date}}</td>
           <td>{{cal.calories}}</td>
         </tr>
         {% endfor %}
     </tbody>
   </table>
{% endblock %}
```

For the _livefeed_ route we just render our __lf.html__ template, which contains all the necessary js code to interact with socketio.

```html
{% extends "base.html" %}
{% block scripts %}
{{super()}}
<script type="text/javascript" charset="utf-8">
    var socket;

    var my_app={
      dates:[],
      today:[]
    }


    $(document).ready(function(){
        socket = io.connect('http://' + document.domain + ':' + location.port + '/livefeed');
        socket.on('connect', function() {
            socket.emit('joined', {});
        });
        get_week();
        get_data();
        socket.on('stats_vals', function(data) {
            console.log(data.data);
            var weights=data.data.weight;
            var calories=data.data.calories;
            var activities=data.data.activities;

            var ww=$('#ww').find('td');
            var wc=$('#wc').find('td');
            var wa=$('#wa').find('td');

            $.each(weights,function(i,weight) {console.log(weight)});
            $.each(calories,function(i,calorie) {console.log(calorie)});
            $.each(activities,function(i,activity) {console.log(activity)});

            $.each(my_app.dates, function(i, date){
              console.log(i, date);
              if (date<=my_app.today){
              ww[i].innerText='X';
              wc[i].innerText='X';
              wa[i].innerText='X';}

              $.each(weights, function(j, weight){
                if (weight.date==date) {
                  console.log(weight,i);
                  ww[i].innerText=weight.weight;
                }
              });

              $.each(calories, function(j, calorie){
                if (calorie.date==date) {
                  console.log(calorie,i);
                  wc[i].innerText=calorie.calories;
                }
              });

              $.each(activities, function(j, activity){
                if (activity.date==date) {
                  console.log(activity,i);
                  wa[i].innerText=activity.distance;
                }
              });

            });
        });

        socket.on('dates', function(data){
          console.log(data.data);
          var theads=$('#STATS').find('thead tr').children();
          my_app.dates=data.data;
          my_app.today=data.today;
          console.log(data.today)
          $.each(data.data,function(i, cdate){
            theads[i].innerText=cdate;
            console.log(theads[i]);
            console.log(cdate);
            });
          });

        socket.on('my_response', function(data){
          console.log(data);
        });
    });

    function get_data() {
        console.log('button pressed');
        console.log(my_app.dates);
        console.log('pressed');
        socket.emit('get_stats', {});
        };

    function get_week() {
        console.log('button pressed');

        socket.emit('get_week', {});
        };
</script>
{% endblock %}

{% block content %}
    <body class='bg-dark'>
        <table id="STATS" class="table table-dark">
          <thead>
            <th class='text-center'></th>
            <th class='text-center'></th>
            <th class='text-center'></th>
            <th class='text-center'></th>
            <th class='text-center'></th>
            <th class='text-center'></th>
            <th class='text-center'></th>
          </thead>
        <tr id='ww'>
          <td class='text-center'></td>
          <td class='text-center'></td>
          <td class='text-center'></td>
          <td class='text-center'></td>
          <td class='text-center'></td>
          <td class='text-center'></td>
          <td class='text-center'></td>
        </tr>
        <tr id='wc'>
          <td class='text-center'></td>
          <td class='text-center'></td>
          <td class='text-center'></td>
          <td class='text-center'></td>
          <td class='text-center'></td>
          <td class='text-center'></td>
          <td class='text-center'></td>
        </tr>
        <tr id='wa'>
          <td class='text-center'></td>
          <td class='text-center'></td>
          <td class='text-center'></td>
          <td class='text-center'></td>
          <td class='text-center'></td>
          <td class='text-center'></td>
          <td class='text-center'></td>
        </tr>
      </table>
      <button onclick="get_week();" type="button" class="btn btn-primary">REFRESH DATES</button>
      <button onclick="get_data();" type="button" class="btn btn-primary">REFRESH DATA </button>

    </body>
{% endblock content %}
```
The important js code is contained within `$(docment).ready()`. This fires up our event listeners and joins our _livefeed_ namespace.

```javascript
socket.on('stats_vals', function(data) {
    console.log(data.data);
    var weights=data.data.weight;
    var calories=data.data.calories;
    var activities=data.data.activities;

    var ww=$('#ww').find('td');
    var wc=$('#wc').find('td');
    var wa=$('#wa').find('td');

    $.each(weights,function(i,weight) {console.log(weight)});
    $.each(calories,function(i,calorie) {console.log(calorie)});
    $.each(activities,function(i,activity) {console.log(activity)});

    $.each(my_app.dates, function(i, date){
      console.log(i, date);
      if (date<=my_app.today){
      ww[i].innerText='X';
      wc[i].innerText='X';
      wa[i].innerText='X';}

      $.each(weights, function(j, weight){
        if (weight.date==date) {
          console.log(weight,i);
          ww[i].innerText=weight.weight;
        }
      });

      $.each(calories, function(j, calorie){
        if (calorie.date==date) {
          console.log(calorie,i);
          wc[i].innerText=calorie.calories;
        }
      });

      $.each(activities, function(j, activity){
        if (activity.date==date) {
          console.log(activity,i);
          wa[i].innerText=activity.distance;
        }
      });

    });
});
```
When the event _stats\_vals_ is fired. We unpack the data json and separate into our individual values. We then replace the corresponding values into inner text values of the correct row cells. We also iterate over the dates of the week and replace with X for values that do not exist (meaning the activity or weight measurement didn't take place).

We also need to modify our __stats\_con.py__ script to pull from enviornmental values rather than hard code our code. To get the environmental variables we use `os.environ.get`.

```python
self._client_id=os.environ.get('FITBIT_CLIENT_ID')
self._client_secret=os.environ.get('FITBIT_CLIENT_SECRET')
```

## Additional Code updates
Now that we have a the Flask application wrapped up we will update our _Prefect_ updater to use the flask application by pushing the application context.

```python
from app import create_app, db
from app.stats.models import Strava_Activity, Fitbit_Weight, Fitbit_Calories
.
.
.
app = create_app('config.Config')
app.app_context().push()
```
Finally we also need to create a new configuration. This is done by modifying __config.py__.

```Python
class Config:
    """Set Flask configuration vars."""

    # General Config
    TESTING = True
    DEBUG = True
    SECRET_KEY = 'WHATEVER'
    SESSION_COOKIE_NAME = 'my_cookie'

    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI',
                                             'postgresql+psycopg2://test:test@0.0.0.0:5401/test')
    SQLALCHEMY_USERNAME = 'test'
    SQLALCHEMY_PASSWORD = 'test'
    SQLALCHEMY_DATABASE_NAME = 'test'
    SQLALCHEMY_TABLE = 'migrations'
    SQLALCHEMY_DB_SCHEMA = 'public'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
```

## Putting it all together
Now that we have all our pieces we want to spin up a docker container with all our services.

Our _docker-compose_ file is pretty straight forward.
```Dockerfile
version: '3.6'

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile_server
    depends_on:
      - db
    environment:
      STAGE: test
      SQLALCHEMY_DATABASE_URI: postgresql+psycopg2://test:test@db/test
    networks:
      - default
    ports:
      - 5000:5000
    volumes:
      - ./app:/usr/src/app/app
      - ./migrations:/usr/src/app/migrations
    restart: always

  updater:
    build:
      context: .
      dockerfile: Dockerfile_updater
    depends_on:
      - db
    environment:
      SQLALCHEMY_DATABASE_URI: postgresql://test:test@db/test
      FITBIT_CLIENT_ID: ###
      FITBIT_CLIENT_SECRET: ###
      STRAVA_CLIENT_ID: ###
      STRAVA_CLIENT_SECRET: ###
    volumes:
      - ./creds:/usr/src/app/creds
    networks:
      - default
    restart: always

  db:
    environment:
      POSTGRES_USER: test
      POSTGRES_PASSWORD: test
      POSTGRES_DB: test
    image: postgres:latest
    networks:
      - default
    ports:
      - 5405:5432
    restart: always
    volumes:
      - pgdata:/var/lib/postgresql/data

volumes:
  pgdata:
    driver: local
```

We define 2 services, webapp and updater which depend on our db.
The dockerfiles are also relatively simple
For the webapp:
```Dockerfile
# pull official base image
FROM python:3.7-slim-buster

RUN apt-get update && \
    apt-get install -y dos2unix

# set work directory
WORKDIR /usr/src/app

# install dependencies
RUN pip install --upgrade pip
COPY ./requirements.txt /usr/src/app/requirements.txt
RUN pip install -r requirements.txt
RUN pip install gunicorn
RUN pip install python-dotenv

# copy project
COPY . /usr/src/app/
RUN chmod +x docker-entrypoint.sh

RUN dos2unix docker-entrypoint.sh
EXPOSE 5000

RUN ls

ENTRYPOINT ["./docker-entrypoint.sh"]
```

with the docker entrypoint handling our DB Migration before starting up.

```sh
#!/bin/sh
set -e
echo --------------------
echo Going to Create database
echo --------------------
export FLASK_APP=wsgi.py
if [ ! -d "migrations" ]; then
    echo --------------------
    echo INIT THE migrations folder
    echo --------------------
    export FLASK_APP=wsgi.py; flask db init
fi
flask db init
echo --------------------
echo Generate migration DDL code
echo --------------------
flask db migrate
echo --------------------
echo Run the DDL code and migrate
echo --------------------
echo --------------------
echo This is the DDL code that will be run
echo --------------------
flask db upgrade

exec gunicorn --bind 0.0.0.0:5000 --worker-class=eventlet -w 2 wsgi:app

```
We use gunicorn with eventlet to serve our app and bind it to 0.0.0.0:5000

__wsgi.py__ is in charge of creating our app.

```python
from app import create_app, socketio

app = create_app('config.Config')
if __name__ =='__main__':
    socketio.run(app)
```

As for our updater the dockerfile for our updater

```Dockerfile
# pull official base image
FROM python:3.7-slim-buster

RUN apt-get update && \
    apt-get install -y gcc && \
    apt-get install -y dos2unix

# set work directory
WORKDIR /usr/src/app

# install dependencies
RUN pip install --upgrade pip
COPY ./requirements_updater.txt /usr/src/app/requirements_updater.txt
RUN pip install -r requirements_updater.txt

# copy project
COPY . /usr/src/app/
RUN chmod +x docker-updater-entrypoint.sh

RUN dos2unix docker-updater-entrypoint.sh

CMD ["tasks.py"]
ENTRYPOINT ["python"]

```

Now if we navigate to localhost:5000/stats/livefeed we will see a calendar view with all our stats. ( I )
