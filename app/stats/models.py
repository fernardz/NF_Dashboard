from .. import Base
from sqlalchemy import BigInteger, Column, String, Integer, ForeignKey, Float, DateTime, TIMESTAMP, func, Time

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
