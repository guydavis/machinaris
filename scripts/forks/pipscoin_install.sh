#!/bin/env bash
#
# Dead fork, developer removed it from Github.
# Installs Pipscoin as per https://github.com/Pipscoin-Network/pipscoin-blockchain
#

PIPSCOIN_BRANCH=$1
# On 2023-01-17
HASH=3017cde5f8c463f5e494c5c1e258dd2bf8281fee

if [ -z ${PIPSCOIN_BRANCH} ]; then
    echo 'Skipping Pipscoin install as not requested.'
else
    git clone --branch ${PIPSCOIN_BRANCH} --recurse-submodules https://github.com/Pipscoin-Network/pipscoin-blockchain.git /pipscoin-blockchain 
    cd /pipscoin-blockchain 
    git submodule update --init mozilla-ca
    git checkout $HASH
    chmod +x install.sh
    # 2022-07-20: Python needs 'packaging==21.3'
    sed -i 's/packaging==21.0/packaging==21.3/g' setup.py
    # Log "Added Coins" at info, not debug level.  See: https://github.com/Chia-Network/chia-blockchain/issues/11955
    sed -i -e 's/^        self.log.debug($/        self.log.info(/g' pipscoin/wallet/wallet_state_manager.py
    /usr/bin/sh ./install.sh

    if [ ! -d /chia-blockchain/venv ]; then
        cd /
        rmdir /chia-blockchain
        ln -s /pipscoin-blockchain /chia-blockchain
        ln -s /pipscoin-blockchain/venv/bin/pipscoin /chia-blockchain/venv/bin/chia
    fi
fi
