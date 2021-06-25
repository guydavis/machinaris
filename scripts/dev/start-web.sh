#!/bin/env bash
#
# Launch WebUI in DEV mode from within container.  
# Runs in foreground of shell.
#

echo 'Starting Machinaris...'
mkdir -p /root/.chia/machinaris/logs
cd /code/machinaris

/chia-blockchain/venv/bin/gunicorn \
    --reload \
    --bind 0.0.0.0:8926 \
    --timeout 90 \
    --log-level=info \
    --workers=2 \
    web:app
