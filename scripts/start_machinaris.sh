#!/bin/env bash
#
# Configures Chia and Plotman, then launches Machinaris web server
#

echo 'Configuring Plotman...'
mkdir -p /root/.chia/plotman/logs
if [[ "${blockchains}" == 'chives' ]]; then
    cp -f /machinaris/config/plotman.sample-chives.yaml /root/.chia/plotman/plotman.sample.yaml
    cp -n /machinaris/config/plotman.sample-chives.yaml /root/.chia/plotman/plotman.yaml
elif [[ "${blockchains}" == 'mmx' ]]; then
    cp -f /machinaris/config/plotman.sample-mmx.yaml /root/.chia/plotman/plotman.sample.yaml
    cp -n /machinaris/config/plotman.sample-mmx.yaml /root/.chia/plotman/plotman.yaml
else # If Chia
    cp -f /machinaris/config/plotman.sample.yaml /root/.chia/plotman/plotman.sample.yaml
    cp -n /machinaris/config/plotman.sample.yaml /root/.chia/plotman/plotman.yaml
    if [ ${farmer_pk} != 'null' ]; then
        sed -i "s/^.*farmer_pk: REPLACE_WITH_THE_REAL_VALUE.*$/        farmer_pk: ${farmer_pk}/g" /root/.chia/plotman/plotman.yaml
    fi
    if [ ${pool_pk} != 'null' ]; then
        sed -i "s/^.*pool_pk: REPLACE_WITH_THE_REAL_VALUE.*$/        pool_pk: ${pool_pk}/g" /root/.chia/plotman/plotman.yaml
    fi
    if [ ${pool_contract_address} != 'null' ]; then
        sed -i "s/^.*pool_contract_address: REPLACE_WITH_THE_REAL_VALUE.*$/        #pool_contract_address: ${pool_contract_address}/g" /root/.chia/plotman/plotman.yaml
    fi
fi
# Import ssh key if exists
if [ -f "/id_rsa" ]; then
    echo "Importing SSH key at /id_rsa volume mount."
    mkdir -p ~/.ssh/
    cp -f /id_rsa ~/.ssh/id_rsa
    cat > ~/.ssh/config <<'_EOF'
    Host *
      StrictHostKeyChecking no
_EOF
    chmod 700 ~/.ssh
    chmod 600 ~/.ssh/*
fi

# Even standalone plotting mode needs database setup
. /machinaris/scripts/setup_databases.sh

mkdir -p /root/.chia/machinaris/config
mkdir -p /root/.chia/machinaris/logs
cd /machinaris
if [ $FLASK_ENV == "development" ];
then
    LOG_LEVEL='debug'
    RELOAD='--reload'
else
    LOG_LEVEL='info'
    RELOAD=''
fi

# Kill gunicorn if already running to allow restart
api_pid=$(pidof 'gunicorn: master [api:app]')
if [ ! -z $api_pid ]; then 
    kill $api_pid
fi
echo 'Starting Machinaris API server...'
. /machinaris/scripts/config_api_server.sh
/chia-blockchain/venv/bin/gunicorn ${RELOAD} \
    --bind 0.0.0.0:${worker_api_port:-8927} --timeout 90 \
    --log-level=${LOG_LEVEL} \
    --workers=1 \
    --threads=12 \
    --config api/gunicorn.conf.py \
    --log-config api/log.conf \
    api:app &

# Kill gunicorn if already running to allow restart
web_pid=$(pidof 'gunicorn: master [web:app]')
if [ ! -z $web_pid ]; then 
    kill $web_pid
fi
echo 'Starting Machinaris Web server...'
/chia-blockchain/venv/bin/gunicorn ${RELOAD} \
    --bind 0.0.0.0:8926 --timeout 90 \
    --log-level=${LOG_LEVEL} \
    --workers=1 \
    --threads=12 \
    --log-config web/log.conf \
    web:app &

echo 'Completed startup.  Browse to port 8926.'

# For later dev if needed during troubleshooting
chmod 755 /machinaris/scripts/dev/*.sh
