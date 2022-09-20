#!/bin/env bash
#
# Installs fd-cli tool: https://github.com/Flora-Network/fd-cli
# Used to recover pool plot rewards (7/8) on the forks
# Not needed on either the Chia or Chives images, only other forks.
#

# On 2021-11-08
HASH=c9f562728acde289d3406d5cdc5a1139fd4267c8

FDCLI_BRANCH=$1

if [[ ${mode} == 'fullnode' ]]; then
    if [[ "${blockchains}" != 'chia' ]] && [[ "${blockchains}" != 'chives' ]] && [[ "${blockchains}" != 'mmx' ]]; then
        cd /
        git clone --branch ${FDCLI_BRANCH} https://github.com/guydavis/flora-dev-cli.git
        cd flora-dev-cli
        git checkout $HASH
        pip install -e . --extra-index-url https://pypi.chia.net/simple/
    fi
fi