#!/bin/env bash
#
# Installs fd-cli tool used to recover pool plot wins on the forks
# Not needed on either the Chia or Chives images, only other forks.
#

if [[ -z ${CHIA_BRANCH} ]] && [[ -z ${CHIVES_BRANCH} ]]; then
    cd /
    git clone https://github.com/Flora-Network/fd-cli.git
    cd fd-cli
    pip install -e . --extra-index-url https://pypi.chia.net/simple/
fi