import os
import tempfile

class Test_Config:
    SQLALCHEMY_DATABASE_URI = 'postgresql://usr:pass@localhost:5432/sqlalchemy'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class Test_Updater:
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI',
                                             'postgresql+psycopg2://test:test@0.0.0.0:5401/test')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class Config:
    """Set Flask configuration vars."""

    # General Config
    TESTING = True
    DEBUG = True
    SECRET_KEY = b'_5#y2L"F4Q8z\n\xec]/'
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
