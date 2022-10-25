#!/bin/env bash
#
# Installs Machinaris for the WebUI
#

echo 'Installing Machinaris...'

cd /chia-blockchain

venv/bin/pip3 install -r /machinaris/docker/requirements.txt

cp -f /machinaris/docker/entrypoint.sh /chia-blockchain/ 

chmod 755 /machinaris/scripts/* /chia-blockchain/entrypoint.sh

tee /etc/logrotate.d/machinaris >/dev/null <<EOF
/root/.chia/machinaris/logs/apisrv.log {
  rotate 7
  daily
}
/root/.chia/machinaris/logs/webui.log {
  rotate 7
  daily
}
EOF