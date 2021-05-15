#!/bin/env bash
#
# Configures Chia and Plotman, then launches Machinaris web server
#

echo 'Configuring Chia...'
#sed -i 's/log_stdout: false/log_stdout: true/g' /root/.chia/mainnet/config/config.yaml
sed -i 's/log_level: WARNING/log_level: INFO/g' /root/.chia/mainnet/config/config.yaml

echo 'Configuring Plotman...'
mkdir -p /root/.chia/plotman
mkdir -p /root/.chia/logs
cp -n /machinaris/config/plotman.sample.yaml /root/.chia/plotman/plotman.yaml

echo 'Starting Machinaris...'
if [ $FLASK_ENV == "development" ];
then
    /chia-blockchain/venv/bin/gunicorn --reload --bind 0.0.0.0:8926 run:app > /root/.chia/logs/machinaris.log 2>&1 &
else
    /chia-blockchain/venv/bin/gunicorn --bind 0.0.0.0:8926 run:app > /root/.chia/logs/machinaris.log 2>&1 &
fi
echo 'Completed container startup.  Browse to port 8926.'