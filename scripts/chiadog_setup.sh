#!/bin/env bash
#
# Installs Chiadog for log monitoring and alerting
#

CHIADOG_BRANCH=dev

if [[ ${mode} == 'fullnode' ]] || [[ ${mode} =~ "harvester" ]]; then
    if [[ ! -f /chiadog/main.py ]]; then
        echo 'Installing Chiadog...'
        cd /
        git clone --branch ${CHIADOG_BRANCH} https://github.com/guydavis/chiadog.git
        cd /chia-blockchain/
        # Chia-blockchain needs PyYAML=5.4.1 but Chiadog wants exactly 5.4
        sed -i 's/==5.4/~=5.4/g' /chiadog/requirements.txt
        # Also, as per Chiadog integrations page, the MQTT integration needs
        # https://github.com/martomi/chiadog/blob/main/INTEGRATIONS.md
        printf "\npaho-mqtt" >> /chiadog/requirements.txt
        # Now install Chiadog python dependencies
        venv/bin/pip3 install -r /chiadog/requirements.txt
    fi
    echo 'Configuring Chiadog...'
    mkdir -p /root/.chia/chiadog/logs
    cp -n /machinaris/config/chiadog/${blockchains}.sample.yaml /root/.chia/chiadog/config.yaml
    sed -i "s/\$HOSTNAME/$HOSTNAME/g" /root/.chia/chiadog/config.yaml
    cp -f /machinaris/scripts/chiadog_notifier.sh /root/.chia/chiadog/notifier.sh && chmod 755 /root/.chia/chiadog/notifier.sh
    echo 'Starting Chiadog...'
    cd /chiadog
    chiadog_pids=$(pidof python3)
    if [[ ! -z $chiadog_pids ]]; then
        kill $chiadog_pids
    fi
    /chia-blockchain/venv/bin/python3 -u main.py --config /root/.chia/chiadog/config.yaml > /root/.chia/chiadog/logs/chiadog.log 2>&1 &
fi
