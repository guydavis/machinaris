#!/bin/env bash
#
# Installs Coffee as per https://github.com/coffee-network/coffee-blockchain
#

COFFEE_BRANCH=$1
# On 2023-01-02
HASH=0b2678d3d64722e787e6ee35a690ed6503a5d08c

if [ -z ${COFFEE_BRANCH} ]; then
    echo 'Skipping Coffee install as not requested.'
else
    rm -rf /root/.cache
    git clone --branch ${COFFEE_BRANCH} --single-branch https://github.com/Coffee-Network/coffee-blockchain.git /coffee-blockchain
    cd /coffee-blockchain 
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
        ln -s /coffee-blockchain /chia-blockchain
        ln -s /coffee-blockchain/venv/bin/sit /chia-blockchain/venv/bin/chia
    fi
fi
