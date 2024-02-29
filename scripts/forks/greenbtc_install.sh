#!/bin/env bash
#
# Installs GreenBTC as per https://github.com/greenbtc/greenbtc-blockchain
#

GREENBTC_BRANCH=$1
# On 2024-02-16
HASH=200816a51c24375fadcbcd25a0b1cb7549f61c77

if [ -z ${GREENBTC_BRANCH} ]; then
    echo 'Skipping GreenBTC install as not requested.'
else
    rm -rf /root/.cache
    git clone --branch ${GREENBTC_BRANCH} --single-branch https://github.com/greenbtc/greenbtc-blockchain.git /greenbtc-blockchain
    cd /greenbtc-blockchain 
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
        ln -s /greenbtc-blockchain /chia-blockchain
        ln -s /greenbtc-blockchain/venv/bin/sit /chia-blockchain/venv/bin/chia
    fi
fi
