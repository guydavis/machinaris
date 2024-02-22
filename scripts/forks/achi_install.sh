#!/bin/env bash
#
# Installs Achi as per https://github.com/Achi-Coin/achi-blockchain
#

ACHI_BRANCH=$1
# On 2024-02-08
HASH=e3ca475efb3d7267d3a2eedef8b4897d129aeb5d

if [ -z ${ACHI_BRANCH} ]; then
    echo 'Skipping Achi install as not requested.'
else
    git clone --branch ${ACHI_BRANCH} --recurse-submodules https://github.com/Achi-Coin/achi-blockchain.git /achi-blockchain
    cd /achi-blockchain
    git submodule update --init mozilla-ca 
    git checkout $HASH
    chmod +x install.sh
    /usr/bin/sh ./install.sh

    if [ ! -d /chia-blockchain/venv ]; then
        cd /
        rmdir /chia-blockchain
        ln -s /achi-blockchain /chia-blockchain
        ln -s /achi-blockchain/venv/bin/achi /chia-blockchain/venv/bin/chia
    fi
fi