#!/bin/env bash
#
# Installs One as per https://github.com/xone-network/one-blockchain
#

ONE_BRANCH=$1
# On 2023-02-18
HASH=2af8e2ca14fca70615c47060fc78b9d5942e4e7c

if [ -z ${ONE_BRANCH} ]; then
    echo 'Skipping One install as not requested.'
else
    git clone --branch ${ONE_BRANCH} --recurse-submodules https://github.com/xone-network/one-blockchain.git /one-blockchain 
    cd /one-blockchain 
    git submodule update --init mozilla-ca
    git checkout $HASH
    chmod +x install.sh
    # 2022-07-20: Python needs 'packaging==21.3'
    sed -i 's/packaging==21.0/packaging==21.3/g' setup.py
    # Log "Added Coins" at info, not debug level.  See: https://github.com/Chia-Network/chia-blockchain/issues/11955
    sed -e 's/^        self.log.debug($/        self.log.info(/g' one/wallet/wallet_state_manager.py
    /usr/bin/sh ./install.sh

    if [ ! -d /chia-blockchain/venv ]; then
        cd /
        rmdir /chia-blockchain
        ln -s /one-blockchain /chia-blockchain
        ln -s /one-blockchain/venv/bin/one /chia-blockchain/venv/bin/chia
    fi
fi
