#!/bin/env bash
#
# Installs Chiadog for log monitoring and alerting
#

echo 'Installing Chiadog...'

cd /

git clone https://github.com/martomi/chiadog.git

cd chiadog

venv/bin/pip3 install -r requirements.txt
