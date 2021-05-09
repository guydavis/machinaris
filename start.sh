#!/bin/env bash
#
# Launches Machinaris and configures Plotman
#

echo 'Configuring Plotman...'
mkdir -p /root/.chia/plotman
mkdir -p /root/.chia/logs
cp /machinaris/plotman.sample.yaml /root/.chia/plotman/plotman.yaml

echo 'Starting Machinaris web server...'
if [ $FLASK_ENV == "development" ];
then
    python3 -m flask run --host=0.0.0.0 > /root/.chia/logs/webui.log 2>&1 &
else
    gunicorn --bind 0.0.0.0:5000 run:app > /root/.chia/logs/webui.log 2>&1 &
fi
