#!/bin/env bash
#
# Launch WebUI in DEV mode from within container.  
# NOT IN GIT.  Runs in foreground of shell.
#

echo 'Starting Machinaris...'
mkdir -p /root/.chia/machinaris/logs
cd /code/machinaris
LOG_LEVEL='debug'
RELOAD='--reload'

# To enable SSL, use the Chia self-signed cert
    #--certfile=/root/.chia/mainnet/config/ssl/ca/chia_ca.crt \
    #--keyfile=/root/.chia/mainnet/config/ssl/ca/chia_ca.key \

/chia-blockchain/venv/bin/gunicorn ${RELOAD} \
    --bind 0.0.0.0:8927 --timeout 90 \
    --log-level=${LOG_LEVEL} \
    --workers=2 \
    api:app