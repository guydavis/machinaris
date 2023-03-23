#!/bin/env bash
#
# Installs Chiadog for log monitoring and alerting,
# using an enhanced and supported fork of the original project.
#

CHIADOG_BRANCH=$1

if [[ (${mode} =~ ^fullnode.*  || ${mode} =~ "harvester") && ${blockchains} != 'mmx' ]]; then
    if [[ ! -f /chiadog/main.py ]]; then
        echo 'Installing Chiadog from https://github.com/guydavis/chiadog using branch: ${CHIADOG_BRANCH}'
        cd /
        git clone --branch ${CHIADOG_BRANCH} https://github.com/guydavis/chiadog.git
        cd /chia-blockchain/
        venv/bin/pip3 install -r /chiadog/requirements.txt
    fi
    echo 'Configuring Chiadog...'
    mkdir -p /root/.chia/chiadog/logs
    cp -n /machinaris/config/chiadog/${blockchains}.sample.yaml /root/.chia/chiadog/config.yaml
    sed -i "s/\$HOSTNAME/`hostname -s`/g" /root/.chia/chiadog/config.yaml
    cp -f /machinaris/scripts/chiadog_notifier.sh /root/.chia/chiadog/notifier.sh && chmod 755 /root/.chia/chiadog/notifier.sh
    echo 'Starting Chiadog...'
    cd /chiadog
    chiadog_pids=$(pidof python3)
    if [[ ! -z $chiadog_pids ]]; then
        kill $chiadog_pids
    fi
    /chia-blockchain/venv/bin/python3 -u main.py --config /root/.chia/chiadog/config.yaml > /root/.chia/chiadog/logs/chiadog.log 2>&1 &
fi
