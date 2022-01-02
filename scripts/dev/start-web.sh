#!/bin/env bash
#
# Launch WebUI in DEV mode from within container.  
# Runs in foreground of shell.
#

echo 'Starting Machinaris...'
mkdir -p /root/.chia/machinaris/logs
cd /code/machinaris

if [ $FLASK_ENV == "development" ];
then
    LOG_LEVEL='debug'
    RELOAD='--reload'
else
    LOG_LEVEL='info'
    RELOAD=''
fi

/chia-blockchain/venv/bin/gunicorn ${RELOAD} \
    --bind 0.0.0.0:8926 \
    --timeout 90 \
    --log-level=$LOG_LEVEL \
    --workers=1 \
    --threads=12 \
    --access-logfile - \
    --error-logfile - \
    web:app
