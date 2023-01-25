#!/bin/env bash
#
# Installs Ballcoin as per https://github.com/ball-network/ballcoin-blockchain
#

BALLCOIN_BRANCH=$1
# On 2023-01-16
HASH=1c60346a5f75e9a489a5904db521336fd9d2d769

if [ -z ${BALLCOIN_BRANCH} ]; then
    echo 'Skipping Ballcoin install as not requested.'
else
    rm -rf /root/.cache
    git clone --branch ${BALLCOIN_BRANCH} --single-branch https://github.com/ball-network/ballcoin-blockchain.git /ballcoin-blockchain
    cd /ballcoin-blockchain
    git submodule update --init mozilla-ca
    chmod +x install.sh
    # 2022-07-20: Python needs 'packaging==21.3'
    sed -i 's/packaging==21.0/packaging==21.3/g' setup.py
    /usr/bin/sh ./install.sh

    if [ ! -d /chia-blockchain/venv ]; then
        cd /
        rmdir /chia-blockchain
        ln -s /ballcoin-blockchain /chia-blockchain
        ln -s /ballcoin-blockchain/venv/bin/ballcoin /chia-blockchain/venv/bin/chia
    fi
fi
