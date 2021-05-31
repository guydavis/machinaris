#!/bin/env bash
#
# Installs Chiadog for log monitoring and alerting
#

echo 'Installing Chiadog...'

cd /

git clone https://github.com/martomi/chiadog.git

cd /chia-blockchain/

# Chia-blockchain needs PyYAML=5.4.1 but Chiadog wants exactly 5.4
sed -i 's/==5.4/~=5.4/g' /chiadog/requirements.txt

# Now install Chiadog python dependencies
venv/bin/pip3 install -r /chiadog/requirements.txt
