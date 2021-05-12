#!/bin/env bash
#
# Configures Chia and Plotman, then launches Machinaris web server
#

echo 'Configuring Chia...'
sed -i 's/log_stdout: false/log_stdout: true/g' /root/.chia/mainnet/config/config.yaml
sed -i 's/log_level: WARNING/log_level: INFO/g' /root/.chia/mainnet/config/config.yaml

echo 'Configuring Plotman...'
mkdir -p /root/.chia/plotman
mkdir -p /root/.chia/logs
cp -n /machinaris/plotman.sample.yaml /root/.chia/plotman/plotman.yaml

echo 'Starting Machinaris...'
export FLASK_ENV=development
export FLASK_APP=/machinaris-dev/main.py
if [ $FLASK_ENV == "development" ];
then
    /chia-blockchain/venv/bin/python3 -m flask run --host=0.0.0.0 > /root/.chia/logs/webui.log 2>&1 &
else
    /chia-blockchain/venv/bin/gunicorn --bind 0.0.0.0:5000 run:app > /root/.chia/logs/webui.log 2>&1 &
fi
