#!/bin/env bash
#
# Launch WebUI in DEV mode from within container.  
# Runs in foreground of shell.
#

echo 'Starting Machinaris...'
mkdir -p /root/.chia/machinaris/logs
cd /code/machinaris

# Workaround due to certain users who dislike CDNs for JS libs...
if [ ! -d /code/machinaris/web/static/3rd_party ]; then
    JS_LIBS_BASEPATH=/code/machinaris/web/static/3rd_party . ./scripts/pull_3rd_party_libs.sh
fi

if [ -n $FLASK_DEBUG ];
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
    --log-config scripts/dev/web_log.conf \
    web:app
