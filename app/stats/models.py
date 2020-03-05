from .. import sql as db

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

    def __repr__(self):
        return "<FITBIT WEIGHT '%s', weight='%s', bmi='%s', date='%s'>"%(self.id, self.weight, self.bmi, self.record_date)

class Fitbit_Calories(db.Model):
    __tablename__='fitbit_calories'
    id=db.Column(db.BigInteger(), primary_key=True)
    calories=db.Column(db.Float())
    record_date=db.Column(db.DateTime())
    last_time = db.Column(db.TIMESTAMP, server_default=db.func.now(), onupdate=db.func.current_timestamp())

    def __repr__(self):
        return "<FITBIT Calories '%s', calories='%s', date='%s'>"%(self.id, self.calories, self.record_date)
