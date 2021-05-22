#!/bin/env bash
#
# Installs Chiadog for log monitoring and alerting
#

echo 'Installing Chiadog...'

cd /

git clone https://github.com/martomi/chiadog.git

cd /chia-blockchain/

venv/bin/pip3 install -r /chiadog/requirements.txt
