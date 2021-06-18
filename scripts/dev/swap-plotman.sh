#!/bin/env bash
#
# Launch WebUI in DEV mode from within container.  
# NOT IN GIT.  Runs in foreground of shell.
#

echo 'Swapping to development Plotman...'
cd /chia-blockchain/venv/lib/python3.9/site-packages
if [ -d ./plotman ]; then
    mv ./plotman ./plotman.orig
    ln -s /code/plotman/src/plotman
fi
