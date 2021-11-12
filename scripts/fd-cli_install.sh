#!/bin/env bash
#
# Installs fd-cli tool used to recover pool plot wins on the forks
# Not needed on either the Chia or Chives images, only other forks.
#

# On 2021-11-08
HASH=e99cf3c9d39d0a6c71ee0f92f11034f0b5516df7

if [[ -z ${CHIA_BRANCH} ]] && [[ -z ${CHIVES_BRANCH} ]]; then
    cd /
    git clone https://github.com/Flora-Network/fd-cli.git
    cd fd-cli
    git checkout $HASH
    pip install -e . --extra-index-url https://pypi.chia.net/simple/
fi