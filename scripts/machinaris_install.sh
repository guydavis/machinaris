#!/bin/env bash
#
# Installs Machinaris for the WebUI
#

echo 'Installing Machinaris...'

cd /chia-blockchain

venv/bin/pip3 install -r /machinaris/docker/requirements.txt

cp -f /machinaris/entrypoint.sh /chia-blockchain/ 

chmod 755 /machinaris/scripts/* /chia-blockchain/entrypoint.sh
