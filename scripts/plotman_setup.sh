#!/bin/env bash
#
# Installs Plotman for plotting management; customized for non-interactive use by Machinaris
#

PLOTMAN_BRANCH=development

if [[ (${mode} == 'fullnode' || ${mode} =~ "plotter") && (${blockchains} == 'chia' || ${blockchains} == 'chives' || ${blockchains} == 'mmx') ]]; then
    if [[ ! -f /chia-blockchain/venv/bin/plotman ]]; then
        echo 'Installing Plotman...'
        cd /
        git clone --branch ${PLOTMAN_BRANCH} https://github.com/guydavis/plotman.git
        cd plotman
        /chia-blockchain/venv/bin/python setup.py install
        apt update && apt install -y rsync
    fi
fi