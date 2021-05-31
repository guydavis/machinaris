#!/bin/env bash
#
# Installs Plotman for plotting management
#


cd /chia-blockchain
PLOTMAN_OFFICIAL_URL=https://github.com/ericaltendorf/plotman@main
from="${PLOTMAN_GIT_URL:-${PLOTMAN_OFFICIAL_URL}}"

echo 'Installing Plotman from:${from}...'
venv/bin/pip3 install git+${from} || venv/bin/pip3 install git+${PLOTMAN_OFFICIAL_URL}