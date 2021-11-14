#!/bin/env bash
#
# Installs Plotman for plotting management; customized for non-interactive use by Machinaris
#

PLOTMAN_REPO_URL=https://github.com/guydavis/plotman@development

if [[ ${mode} == 'fullnode' && (${blockchains} == 'chia' || ${blockchains} == 'chives') ]] || [[ ${mode} =~ "plotter" ]]; then
    if [[ ! -f /chia-blockchain/venv/bin/plotman ]]; then
        cd /chia-blockchain
        echo 'Installing Plotman...'
        venv/bin/pip3 install git+${PLOTMAN_REPO_URL} || venv/bin/pip3 install git+${PLOTMAN_REPO_URL}
        apt update && apt install -y rsync
    fi
    # Start plotting automatically if requested (not the default)
    if [ ${AUTO_PLOT,,} = "true" ]; then
        nohup plotman plot >> /root/.chia/plotman/logs/plotman.log 2>&1 &
    fi
fi