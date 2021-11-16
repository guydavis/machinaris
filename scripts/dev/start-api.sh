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

# To enable SSL, use the Chia self-signed cert
    #--certfile=/root/.chia/mainnet/config/ssl/ca/chia_ca.crt \
    #--keyfile=/root/.chia/mainnet/config/ssl/ca/chia_ca.key \

/chia-blockchain/venv/bin/gunicorn ${RELOAD} \
    --bind 0.0.0.0:${worker_api_port:-8927} \
    --timeout 90 \
    --log-level=${LOG_LEVEL} \
    --workers=2 \
    --config api/gunicorn.conf.py \
    --error-logfile - \
    --access-logfile - \
    api:app