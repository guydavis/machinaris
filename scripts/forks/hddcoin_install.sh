#!/bin/env bash
#
# Installs HDDCoin as per https://github.com/HDDcoin-Network/hddcoin-blockchain
#

HDDCOIN_BRANCH=$1
# On 2023-07-17
HASH=e7004bd47b285158b2ede704dce55c91b108283f

if [ -z ${HDDCOIN_BRANCH} ]; then
    echo 'Skipping HDDCoin install as not requested.'
else
    git clone --branch ${HDDCOIN_BRANCH} --recurse-submodules https://github.com/HDDcoin-Network/hddcoin-blockchain.git /hddcoin-blockchain
    cd /hddcoin-blockchain
    git submodule update --init mozilla-ca 
    git checkout $HASH
    chmod +x install.sh
    /usr/bin/sh ./install.sh

    if [ ! -d /chia-blockchain/venv ]; then
        cd /
        rmdir /chia-blockchain
        ln -s /hddcoin-blockchain /chia-blockchain
        ln -s /hddcoin-blockchain/venv/bin/hddcoin /chia-blockchain/venv/bin/chia
    fi
fi