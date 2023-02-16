#!/bin/env bash
#
# Installs Gold as per https://github.com/goldcoin-gl/gold-blockchain
#

GOLD_BRANCH=$1
# On 2022-08-07
HASH=8f3bd229813a820e4b9d2e4cd69a28c00c27b7d2

if [ -z ${GOLD_BRANCH} ]; then
    echo 'Skipping Gold install as not requested.'
else
    rm -rf /root/.cache
    git clone --branch ${GOLD_BRANCH} --single-branch https://github.com/goldcoin-gl/gold-blockchain.git /gold-blockchain
    cd /gold-blockchain 
    git submodule update --init mozilla-ca 
    git checkout $HASH
    chmod +x install.sh
    # 2022-01-30: pip broke due to https://github.com/pypa/pip/issues/10825
    sed -i 's/upgrade\ pip$/upgrade\ "pip<22.0"/' install.sh
    # 2022-07-20: Python needs 'packaging==21.3'
    sed -i 's/packaging==21.0/packaging==21.3/g' setup.py
    /usr/bin/sh ./install.sh

    if [ ! -d /chia-blockchain/venv ]; then
        cd /
        rmdir /chia-blockchain
        ln -s /gold-blockchain /chia-blockchain
        ln -s /gold-blockchain/venv/bin/gold /chia-blockchain/venv/bin/chia
    fi
fi
