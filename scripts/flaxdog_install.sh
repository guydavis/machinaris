#!/bin/env bash
#
# Installs Flaxdog for log monitoring and alerting
#

echo 'Installing Flaxdog...'

cd /

git clone https://github.com/langhorst/flaxdog.git

# Temporary patch for spam about partial proofs
# https://github.com/martomi/chiadog/issues/252#issuecomment-877416135
#cd /flaxdog/src/flax_log/handlers/
#sed -i 's/FoundProofs(),//g' harvester_activity_handler.py

cd /flax-blockchain/

# Chia-blockchain needs PyYAML=5.4.1 but Chiadog wants exactly 5.4
sed -i 's/==5.4/~=5.4/g' /flaxdog/requirements.txt

# Also, as per Chiadog integrations page, the MQTT integration needs
# https://github.com/martomi/chiadog/blob/main/INTEGRATIONS.md
printf "\npaho-mqtt" >> /flaxdog/requirements.txt

# Now install Chiadog python dependencies
venv/bin/pip3 install -r /flaxdog/requirements.txt
