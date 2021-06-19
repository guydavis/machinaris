#!/bin/env bash
#
# Launch WebUI in DEV mode from within container.  
# Runs in foreground of shell.
#

echo 'Starting Machinaris...'
mkdir -p /root/.chia/machinaris/logs
cd /code/machinaris
LOG_LEVEL='info'
RELOAD='--reload'

# To enable SSL, use the Chia self-signed cert
    #--certfile=/root/.chia/mainnet/config/ssl/ca/chia_ca.crt \
    #--keyfile=/root/.chia/mainnet/config/ssl/ca/chia_ca.key \

/chia-blockchain/venv/bin/gunicorn ${RELOAD} \
    --bind 0.0.0.0:8927 --timeout 90 \
    --log-level=${LOG_LEVEL} \
    --workers=2 \
    --config api/gunicorn.conf.py \
    api:app