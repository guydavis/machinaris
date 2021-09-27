#!/bin/env bash
#
# Installs Chiadog for log monitoring and alerting
#

CHIADOG_BRANCH=main

echo 'Installing Chiadog...'

cd /

git clone --branch ${CHIADOG_BRANCH} https://github.com/guydavis/chiadog.git

cd /chia-blockchain/

# Chia-blockchain needs PyYAML=5.4.1 but Chiadog wants exactly 5.4
sed -i 's/==5.4/~=5.4/g' /chiadog/requirements.txt

# Also, as per Chiadog integrations page, the MQTT integration needs
# https://github.com/martomi/chiadog/blob/main/INTEGRATIONS.md
printf "\npaho-mqtt" >> /chiadog/requirements.txt

# Now install Chiadog python dependencies
venv/bin/pip3 install -r /chiadog/requirements.txt
