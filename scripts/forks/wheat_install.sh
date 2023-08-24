#!/bin/env bash
#
# Installs Wheat as per https://github.com/wheatnetwork/wheat-blockchain
#

WHEAT_BRANCH=$1
# On 2023-07-20
HASH=5185edcd0ae333da6c157783cf4d1f19ee0a252d

if [ -z ${WHEAT_BRANCH} ]; then
    echo 'Skipping Wheat install as not requested.'
else
    rm -rf /root/.cache
    git clone --branch ${WHEAT_BRANCH} --single-branch https://github.com/wheatnetwork/wheat-blockchain.git /wheat-blockchain
    cd /wheat-blockchain 
    git submodule update --init mozilla-ca 
    git checkout $HASH
    chmod +x install.sh
    /usr/bin/sh ./install.sh

    if [ ! -d /chia-blockchain/venv ]; then
        cd /
        rmdir /chia-blockchain
        ln -s /wheat-blockchain /chia-blockchain
        ln -s /wheat-blockchain/venv/bin/wheat /chia-blockchain/venv/bin/chia
    fi
fi
