#!/bin/env bash
#
# Configures Chia and Plotman, then launches Machinaris web server
#

echo 'Configuring Chia...'
sed -i 's/log_stdout: true/log_stdout: false/g' /root/.chia/mainnet/config/config.yaml
sed -i 's/log_level: WARNING/log_level: INFO/g' /root/.chia/mainnet/config/config.yaml

echo 'Configuring Plotman...'
mkdir -p /root/.chia/plotman/logs
# Check for existing, old versions of plotman.yaml and migrate them, else use default
/chia-blockchain/venv/bin/python3 /machinaris/scripts/plotman_migrate.py
if [ ${farmer_pk} != 'null' ]; then
    sed -i "s/^.*farmer_pk:.*$/        farmer_pk: ${farmer_pk}/g" /root/.chia/plotman/plotman.yaml
fi
if [ ${pool_pk} != 'null' ]; then
    sed -i "s/^.*pool_pk:.*$/        pool_pk: ${pool_pk}/g" /root/.chia/plotman/plotman.yaml
fi

if [ "${mode}" != "plotter" ]; then
    echo 'Configuring Chiadog...'
    mkdir -p /root/.chia/chiadog/logs
    cp -n /machinaris/config/chiadog.sample.yaml /root/.chia/chiadog/config.yaml
    cp -f /machinaris/scripts/chiadog_notifier.sh /root/.chia/chiadog/notifier.sh && chmod 755 /root/.chia/chiadog/notifier.sh
    . /machinaris/scripts/setup_databases.sh

    echo 'Starting Chiadog...'
    cd /chiadog
    chiadog_pid=$(pidof python3)
    if [ ! -z $chiadog_pid ]; then
        kill $chiadog_pid
    fi
    /chia-blockchain/venv/bin/python3 -u main.py --config /root/.chia/chiadog/config.yaml > /root/.chia/chiadog/logs/chiadog.log 2>&1 &
fi

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
/chia-blockchain/venv/bin/gunicorn ${RELOAD} \
    --bind 0.0.0.0:8927 --timeout 90 \
    --log-level=${LOG_LEVEL} \
    --workers=2 \
    --config api/gunicorn.conf.py \
    api:app > /root/.chia/machinaris/logs/apisrv.log 2>&1 &

# Kill gunicorn if already running to allow restart
web_pid=$(pidof 'gunicorn: master [web:app]')
if [ ! -z $web_pid ]; then 
    kill $web_pid
fi
echo 'Starting Machinaris Web server...'
/chia-blockchain/venv/bin/gunicorn ${RELOAD} \
    --bind 0.0.0.0:8926 --timeout 90 \
    --log-level=${LOG_LEVEL} \
    --workers=2 \
    web:app > /root/.chia/machinaris/logs/webui.log 2>&1 &

echo 'Completed startup.  Browse to port 8926.'

# For later dev if needed during troubleshooting
chmod 755 /machinaris/scripts/dev/*.sh
