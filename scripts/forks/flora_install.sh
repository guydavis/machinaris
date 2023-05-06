#!/bin/env bash
#
# Installs Flora as per https://github.com/ageorge95/flora-blockchain.git
#

FLORA_BRANCH=$1
# On 2023-05-06
HASH=f3ee4b1a2c09c3449cab31bfb814b2551ae13b45

if [ -z ${FLORA_BRANCH} ]; then
    echo 'Skipping Flora install as not requested.'
else
    rm -rf /root/.cache
    git clone --branch ${FLORA_BRANCH} --single-branch https://github.com/ageorge95/flora-blockchain.git /flora-blockchain
    cd /flora-blockchain 
    git submodule update --init mozilla-ca 
    git checkout $HASH
    chmod +x install.sh

    # Log "Added Coins" at info, not debug level.  See: https://github.com/Chia-Network/chia-blockchain/issues/11955
    sed -i -e 's/^        self.log.debug($/        self.log.info(/g' flora/wallet/wallet_state_manager.py

    /usr/bin/sh ./install.sh

    if [ ! -d /chia-blockchain/venv ]; then
        cd /
        rmdir /chia-blockchain
        ln -s /flora-blockchain /chia-blockchain
        ln -s /flora-blockchain/venv/bin/flora /chia-blockchain/venv/bin/chia
    fi
fi
