#!/bin/sh
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
