#!/bin/env bash
#
# Installs fd-cli tool used to recover pool plot wins on the forks
#

if [ -z ${CHIA_BRANCH} ]; then
	echo 'Skipping fd-cli install as not Chia image.'
else
    cd /
    git clone https://github.com/Flora-Network/fd-cli.git
    cd fd-cli
    #python3 -m venv venv
    #source venv/bin/activate
    pip install -e . --extra-index-url https://pypi.chia.net/simple/
    #deactivate
fi