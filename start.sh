#!/bin/env bash
#
# Launches Machinaris
#
echo 'Starting Machinaris web server...'
if [ $FLASK_ENV == "development" ];
then
    python3 -m flask run --host=0.0.0.0
else
    gunicorn --bind 0.0.0.0:5000 run:app
fi
