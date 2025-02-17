#!/bin/env bash
#
# Installs Plotman for plotting management; customized for non-interactive use by Machinaris
#

PLOTMAN_BRANCH=$1

if [[ (${mode} =~ ^fullnode.*  || ${mode} =~ "plotter") && (${blockchains} == 'chia' || ${blockchains} == 'chives' || ${blockchains} == 'mmx' || ${blockchains} == 'gigahorse') ]]; then
    if [[ ! -f /chia-blockchain/venv/bin/plotman ]]; then
        echo 'Installing Plotman...'
        cd /
        git clone --branch ${PLOTMAN_BRANCH} https://github.com/guydavis/plotman.git
        cd plotman
        /chia-blockchain/venv/bin/pip install .
        # Workaround for broken dependency ordering
        /chia-blockchain/venv/bin/pip install pendulum~=3.0
        /chia-blockchain/venv/bin/pip install packaging~=24.2
        /chia-blockchain/venv/bin/pip install attrs~=21.2
        /chia-blockchain/venv/bin/pip install desert~=2020.11.18
        /chia-blockchain/venv/bin/pip install appdirs~=1.4
        apt update && apt install -y rsync
        mkdir -p /root/.chia/plotman/logs/archiving
        tee /etc/logrotate.d/plotman >/dev/null <<EOF
/root/.chia/plotman/logs/plotman.log {
  rotate 3
  daily
}
/root/.chia/plotman/logs/archiver.log {
  rotate 3
  daily
}
EOF
    fi
fi