#!/bin/env bash
#
# Installs fd-cli tool: https://github.com/Flora-Network/fd-cli
# Used to recover pool plot rewards (7/8) on the forks
# Not needed on either the Chia or Chives images, only other forks.
#

FDCLI_BRANCH=$1

if [[ ${mode} == 'fullnode' ]]; then
    if [[ "${blockchains}" != 'chia' ]] && [[ "${blockchains}" != 'chives' ]] && [[ "${blockchains}" != 'mmx' ]]; then
        cd /
        git clone --branch ${FDCLI_BRANCH} https://github.com/guydavis/flora-dev-cli.git
        cd flora-dev-cli
        codename=`lsb_release -c -s`
        echo "Building fd-cli on Ubuntu ${codename}..."
        cp requirements_${codename}.txt requirements.txt
        cp setup_${codename}.py setup.py
        pip install -e . --extra-index-url https://pypi.chia.net/simple/
    fi
fi