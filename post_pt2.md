# Building a Fitness Tracking Dashboard with Python. Pt 2 Data Update and SQL Alchemy

Now that we have developed classes to help us interact for both the Fitbit and Strava API, we need a way to store that data where it is easily accessible. In order to do so we will roll out a postgres database on docker and use sqlalchemy to simplify our interactions with the db.

## Project Organization
Since eventually I want to setup a flask website to display the information, I will start setting up the project as a flask application factory and separating into modules. There are much better tutorials out there for how to set it up and I recommend searching for them.
At this point my project structure looks as follows.
```
\app
  \static
    \examples
    \js
  \stats
    __init__.py
    models.py
  \templates
  __init__.py
stats_con.py
tasks.py

```
## Test DB setup
Since we are still in the development stages we choose to roll out a docker based db  (in this case Postgres).

We can spin up the container with the following command
```
docker run --name sqlalchemy-orm-psql -e
POSTGRES_PASSWORD=pass -e POSTGRES_USER=usr -e
POSTGRES_DB=sqlalchemy -p 5432:5432 -d postgres
```
This will initialize postgres database at localhost:5432 a username named **usr** and set its password as **pass**, finally it will also create a database called **sqlalchemy**.

## Creating the sqlalchemy classes
[SQLAlchemy](https://www.sqlalchemy.org/) is a great tool for setting up our database interactions and tables (it also has a very useful flask plugin for down the line).

The first step is setting up classes to allow us to interact with the database and to function as representations of our tables.

Since this isn't a particularly complex projects I only setup one folder to contain my classes under the `stats` folder, making sure to create the `__init__.py` to treat it as a module.

### Upper Level Initialization
Since I will eventually move everything to flask, we want to start enough to it. Under the app subfolder we want to create an `__init__.py` file to initialize properly and allow for imports into the sqlalchemny classes.

All we are doing in this file is creating the database connection and setting its parameters.

We import sqlalchemy and create the engine using the previously created postgres db URI.

```Python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

engine = create_engine('postgresql://usr:pass@localhost:5432/sqlalchemy')
```
We use this engine to create session which allows us to run queries against the database and functions as our main connection to it.

```Python
Session = sessionmaker(bind=engine)
```

Finally we create a `Base`, from the `declarative_base()` function. This creates the base for our classes. This makes sure that the correct Table objects are created and properly maps our objects to the database.

```Python
Base=declarative_base()
```

> This more than likely will be changed when using flask since flask-alchemy has additional functionality tied to using db.Model as opposed to Base=declarative_base()


### Fitbit Classes
Now that we have initialize the connection to our database and created the base factory we can create the actual classes for our data.

First we import our Base object and the necessary sqlalchemy.
```Python
from .. import Base
from sqlalchemy import BigInteger, Column, String, Integer, ForeignKey, Float, DateTime, TIMESTAMP, func, Time

class Fitbit_Weight(Base):
    __tablename__='fitbit_weight'
    id=Column(BigInteger(), primary_key=True)
    weight=Column(Float(), nullable=False)
    bmi=Column(Float())
    fat=Column(Float())
    record_date=Column(DateTime())
    record_time=Column(Time())
    last_time = Column(TIMESTAMP, server_default=func.now(), onupdate=func.current_timestamp())

    def __repr__(self):
        return "<FITBIT WEIGHT '%s', weight='%s', bmi='%s', date='%s'>"%(self.id, self.weight, self.bmi, self.record_date)

class Fitbit_Calories(Base):
    __tablename__='fitbit_calories'
    id=Column(BigInteger(), primary_key=True)
    calories=Column(Float())
    record_date=Column(DateTime())
    last_time = Column(TIMESTAMP, server_default=func.now(), onupdate=func.current_timestamp())

    def __repr__(self):
        return "<FITBIT Calories '%s', calories='%s', date='%s'>"%(self.id, self.calories, self.record_date)
```

The process is pretty self explanatory. The the things to pay attention to is to remember to create a `primary_key` on each table.

w also used the `func` function to make sure that I store the time at which the records are updated.

Finally to assist with debugging and logging to a certain degree, we create a `__repr__` method to allow for a more informative message for each of objects created with these classes.

### Strava Class

The same process is used for the Strava information

```Python
class Strava_Activity(Base):
    __tablename__='strava_activity'
    #index=Column(Integer(), primary_key=True)
    id=Column(BigInteger(), primary_key=True)
    owner=Column(Integer())#Probs Foregin keyring
    activity_type=Column(String(50))
    distance=Column(Float())
    elapsed_time=Column(Float())
    average_speed=Column(Float())
    average_cadence=Column(Float())
    average_heartrate=Column(Float())
    name=Column(String(50))
    utc_offset=Column(Float())
    max_speed=Column(Float())
    max_heartrate=Column(Float())
    total_elevation_gain=Column(Float())
    upload_id=Column(BigInteger())
    moving_time=Column(Float())
    start_date=Column(DateTime())
    start_date_local=Column(DateTime())
    last_time = Column(TIMESTAMP, server_default=func.now(), onupdate=func.current_timestamp())

    def __repr__(self):
        return "<STRAVA ACTIVITY '%s', distance='%s', type='%s', date='%s'>"%(self.id, self.distance, self.activity_type, self.start_date_local)
```

## Storing the data
Now that we have a well defined way to access our database we can get to the process of actually recording the data obtained from our API calls into the db.

The first step is to create all the tables we defined in our sqlalchemy classes if they dont exist.
`Base.metadata.create_all()`

We also initialize our db session with `session=Session()`

Importing the `stats_con.py` classes `Strava` and `Fitbit` we can use the previously defined functions to obtain our information.

```Python
def Update_Strava_Activities():
    # Initialize Strava connection and get the data
    stv=Strava()
    data=stv.get_activities().json()

    # Get the required columns from our Strava Class
    strava_params=[c for c in inspect(Strava_Activity).columns.keys()]

    # Remove the last time parameter as that is autogenerated
    strava_params.remove('last_time')

    #We will first create all our model class instances for Strava_Activity
    acts=[]
    for dic in data:
        #Initialize an empty default dict so we dont get triped up with key missing issues
        d = defaultdict(lambda: None, dic)
        #Rename some columns from the API json so they match our class
        d['owner']=d['athlete']['id']
        d['activity_type']=d['type']

        #Search for values needed in our class in the API json
        update={}
        for val in strava_params:
            update[val]=d[val]

        log.info(update)

        #Initialize our model class from the dictionary
        act=Strava_Activity(**update)
        acts.append(act)

    # Merge our results into the database (I will rewrite all of them for the last 30 items regardless of what it says), at the current moment I don't need to check the API for deleted activities but might in the future.
    for act in acts:
        try:
            with session.begin_nested():
                session.merge(act)
            log.info("Updated: %s"%str(act))
        except:
            log.info("Skipped %s"%str(act))
    session.commit()
    session.flush()
```
First we initialize our Strava connection using our previously developed class.
We obtain our data using `stv.get_activities().json()`. This will return a json with our information.

Since we need to define the values of the  Since we are lazy we actually get the names of the sqlalchemy columns from the sqlalchemy Strava Class. We can do that using `inspect` and pushing into an array.

```Python
strava_params=[c for c in inspec(Strava_Activity).columns.keys()]
```

In the next code block we iterate thru the array and push the values into a default dictionary. The reason we use a default dictionary is to prepolulate with nulls since some activities will not have all the infomrmation. We also use this to rename some of the obtained json values into the correct column name.

We use`**update` to pass a dictionary to initialize our sqlaclhemy object from a dictionary instead of typing it out.

Then we use our session object with begin_nested and try to merge our recods and commit them, this is better explained at [sqlalchemy documentation](https://docs.sqlalchemy.org/en/13/orm/session_transaction.html).

We will also do the same for our Fitbit Weight

```Python
def Update_Fitbit_Weight():
    fbt=Fitbit()
    wdata=fbt.get_weight().json()

    fweight_params=[c for c in inspect(Fitbit_Weight).columns.keys()]
    fweight_params.remove('last_time')

    acts=[]

    for dic in wdata['weight']:
        d = defaultdict(lambda: None, dic)
        d['id']=d['logId']
        d['record_date']=d['date']
        d['record_time']=d['time']

        update={}
        for val in fweight_params:
            update[val]=d[val]

        act=Fitbit_Weight(**update)
        acts.append(act)

    for act in acts:
        try:
            with session.begin_nested():
                session.merge(act)
            log.info("Updated: %s"%str(act))
        except:
            log.info("Skipped %s"%str(act))
    session.commit()
    session.flush()
```
and the Fitbit Calories

```Python
def Update_Fitbit_Calories():
    fbt=Fitbit()
    #The calories dont have an ID so create one out of the date
    cdata=fbt.get_calories().json()
    acts=[]
    for dic in cdata['foods-log-caloriesIn']:
        d = defaultdict(lambda: None, dic)
        update={}
        update['id']=int(datetime.datetime.strptime(d['dateTime'], '%Y-%m-%d').timestamp())
        update['record_date']=d['dateTime']
        update['calories']=d['value']

        act=Fitbit_Calories(**update)
        acts.append(act)

    for act in acts:
        try:
            with session.begin_nested():
                session.merge(act)
            log.info("Updated: %s"%str(act))
        except:
            log.info("Skipped %s"%str(act))
    session.commit()
    session.flush()
```
So now we have a method of storing our data into our database.

## Scheduling our Updates
Finally we probably want to set this to update on a schedule. There are multiple ways of doing this. The most popular being chrontab or something with a celery scheduled worker. I have also been looking at using airflow for stuff like this. However at this moment we just want to keep this simple and for that `Prefect` works pretty well.

All we have to do is create tasks and define a `Flow` and a `Schedule`, we can even set up dependent tasks that way.

So for example we update the `Update_Strava_Activities` function to be a Prefect tasks.

```Python
@task(max_retries=2, retry_delay=timedelta(seconds=2))
def Update_Strava_Activities():
```

Which sets it to retry 2 times with a 2 second delay between retries.
We then define theses tasks inside a flow, tied to a schedule.

```Python
from datetime import timedelta
import prefect
from prefect import Flow, Parameter, task, unmapped
from prefect.schedules import IntervalSchedule

...

schedule = IntervalSchedule(interval=timedelta(minutes=60))

with Flow("Data Updater", schedule) as flow:
    Update_Strava_Activities()
    Update_Fitbit_Weight()
    Update_Fitbit_Calories()
```
This will run both of those tasks independently (so if one fails it wont prevent the other from running) and they will fire off every 60 seconds. All we have to do after is run the flow with `flow.run()` and the script will fire off and update our data every 60 minutes.

In the final part we will modify this basic project and develop a quick flask dashboard to present a calendar view of our weekly stats.
