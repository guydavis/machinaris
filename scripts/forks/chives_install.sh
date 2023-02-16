#!/bin/env bash
#
# Installs Chives as per https://github.com/HiveProject2021/chives-blockchain
# Alternatively, also supports the Foxy port: https://github.com/foxypool/chives-blockchain
#

CHIVES_REPO=$1
CHIVES_BRANCH=$2

if [ -z ${CHIVES_BRANCH} ]; then
    echo 'Skipping Chives install as not requested.'
else
    git clone --branch ${CHIVES_BRANCH} --recurse-submodules ${CHIVES_REPO} /chives-blockchain 
    cd /chives-blockchain
    chmod +x install.sh
    # 2022-07-20: Python needs 'packaging==21.3'
    sed -i 's/packaging==21.0/packaging==21.3/g' setup.py
    /usr/bin/sh ./install.sh

    if [ ! -d /chia-blockchain/venv ]; then
        cd /
        rmdir /chia-blockchain
        ln -s /chives-blockchain /chia-blockchain
        ln -s /chives-blockchain/venv/bin/chives /chia-blockchain/venv/bin/chia
    fi
fi
