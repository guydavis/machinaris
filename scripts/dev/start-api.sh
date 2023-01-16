#!/bin/env bash
#
# Launch WebUI in DEV mode from within container.  
# Runs in foreground of shell.
#

echo 'Starting Machinaris...'
mkdir -p /root/.chia/machinaris/logs
cd /code/machinaris

if [ -n $FLASK_DEBUG ];
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
    --workers=1 \
    --threads=12 \
    --config api/gunicorn.conf.py \
    --log-config scripts/dev/api_log.conf \
    api:app