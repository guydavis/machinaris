#!/bin/env bash
#
# Installs Chiadog for log monitoring and alerting
#

echo 'Installing Chiadog...'

cd /

git clone https://github.com/martomi/chiadog.git

cd chiadog

# Update pip3 to latest version
python3 -m pip install --upgrade pip

# Install dependencies
pip3 install wheel && pip3 install -r requirements.txt
