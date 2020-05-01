#!/bin/sh
set -e
export FLASK_APP=wsgi.py
if [ ! -d "migrations" ]; then
    echo INIT THE MIGRATIONS FOLDER
    export FLASK_APP=wsgi.py; flask db init
fi
#flask db init
flask db migrate
flask db upgrade

exec gunicorn --bind 0.0.0.0:5000 --worker-class=eventlet -w 2 wsgi:app
