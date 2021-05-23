#!/bin/env bash
#
# Installs Plotman for plotting management
#

echo 'Installing Plotman...'

cd /chia-blockchain

venv/bin/pip3 install git+https://github.com/ericaltendorf/plotman@main
