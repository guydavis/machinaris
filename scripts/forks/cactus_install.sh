#!/bin/env bash
#
# Installs Cactus as per https://github.com/Cactus-Network/cactus-blockchain
#

CACTUS_BRANCH=$1
# On 2025-01-15
HASH=4a8cab070bab126c9246d1fb50450062fdf10abd

if [ -z ${CACTUS_BRANCH} ]; then
    echo 'Skipping Cactus install as not requested.'
else
    git clone --branch ${CACTUS_BRANCH} --recurse-submodules https://github.com/Cactus-Network/cactus-blockchain.git /cactus-blockchain 
    cd /cactus-blockchain 
    git submodule update --init mozilla-ca
    git checkout $HASH
    chmod +x install.sh
    # Log "Added Coins" at info, not debug level.  See: https://github.com/Chia-Network/chia-blockchain/issues/11955
    sed -i 's/^        self.log.debug($/        self.log.info(/g' cactus/wallet/wallet_state_manager.py
    
    /usr/bin/sh ./install.sh

    if [ ! -d /chia-blockchain/venv ]; then
        cd /
        rmdir /chia-blockchain
        ln -s /cactus-blockchain /chia-blockchain
        ln -s /cactus-blockchain/venv/bin/cactus /chia-blockchain/venv/bin/chia
    fi
fi
