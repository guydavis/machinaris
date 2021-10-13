#!/bin/env bash
#
# Installs Plotman for plotting management; customized for non-interactive use by Machinaris
#

cd /chia-blockchain
PLOTMAN_REPO_URL=https://github.com/guydavis/plotman@development
from="${PLOTMAN_GIT_URL:-${PLOTMAN_REPO_URL}}"

echo 'Installing Plotman from:${from}...'
venv/bin/pip3 install git+${from} || venv/bin/pip3 install git+${PLOTMAN_REPO_URL}