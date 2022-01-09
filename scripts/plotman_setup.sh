#!/bin/env bash
#
# Installs Plotman for plotting management; customized for non-interactive use by Machinaris
#

PLOTMAN_REPO_URL=https://github.com/guydavis/plotman@development

if [[ (${mode} == 'fullnode' || ${mode} =~ "plotter") && (${blockchains} == 'chia' || ${blockchains} == 'chives' || ${blockchains} == 'mmx') ]]; then
    if [[ ! -f /chia-blockchain/venv/bin/plotman ]]; then
        cd /chia-blockchain
        echo 'Installing Plotman...'
        venv/bin/pip3 install git+${PLOTMAN_REPO_URL} || venv/bin/pip3 install git+${PLOTMAN_REPO_URL}
        apt update && apt install -y rsync
    fi
fi